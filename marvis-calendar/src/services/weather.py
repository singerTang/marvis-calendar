"""Marvis Calendar — 天气服务

使用 wttr.in 免费 API，无需注册和 API Key。
先通过 IP 定位用户城市，再查询天气。
30 分钟缓存，网络降级：超时/失败返回上次缓存 + 提示。
"""

import json
import time
from datetime import date
from typing import Optional

import httpx

# wttr.in 完全免费，无需 API Key
API_BASE = "https://wttr.in"
CACHE_TTL = 30 * 60  # 30 分钟

# 天气图标映射
WEATHER_ICONS = {
    "Sunny": "☀️",
    "Clear": "🌙",
    "Partly cloudy": "⛅",
    "Cloudy": "☁️",
    "Overcast": "☁️",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Light rain": "🌦️",
    "Light Rain Shower": "🌦️",
    "Moderate rain": "🌧️",
    "Heavy rain": "🌧️",
    "Light snow": "🌨️",
    "Moderate snow": "❄️",
    "Heavy snow": "❄️",
    "Thunderstorm": "⛈️",
    "Patchy rain possible": "🌦️",
}

# 中文天气描述映射
WEATHER_CN_MAP = {
    "Sunny": "晴",
    "Clear": "晴",
    "Partly cloudy": "多云",
    "Partly Cloudy": "多云",
    "Cloudy": "阴",
    "Overcast": "阴",
    "Mist": "雾",
    "Fog": "雾",
    "Smoke": "霾",
    "Smoky": "霾",
    "Smoky haze": "霾",
    "Haze": "霾",
    "Light Rain Shower": "小雨",
    "Light rain": "小雨",
    "Light drizzle": "小雨",
    "Patchy light drizzle": "小雨",
    "Patchy light rain": "小雨",
    "Light rain shower": "小雨",
    "Light sleet": "雨夹雪",
    "Light sleet showers": "雨夹雪",
    "Patchy rain": "阵雨",
    "Patchy rain nearby": "阵雨",
    "Patchy rain possible": "阵雨",
    "Moderate rain": "中雨",
    "Moderate or heavy rain shower": "大雨",
    "Moderate or heavy rain with thunder": "雷阵雨",
    "Torrential rain shower": "暴雨",
    "Heavy rain": "大雨",
    "Light snow": "小雪",
    "Patchy light snow": "小雪",
    "Moderate snow": "中雪",
    "Patchy moderate snow": "中雪",
    "Heavy snow": "大雪",
    "Patchy heavy snow": "大雪",
    "Blizzard": "暴雪",
    "Freezing fog": "冻雾",
    "Thunderstorm": "雷阵雨",
    "Thundery outbreaks possible": "雷阵雨",
}


class WeatherService:
    def __init__(self, config_path=None):
        self._config_path = config_path
        self._city: str = ""  # 空表示自动定位
        self._cache: dict = {}
        self._cache_ts: float = 0
        self._configured = True
        self._location_detected = False

    @property
    def configured(self) -> bool:
        return True

    def configure(self, api_key: str, city: str = ""):
        """兼容旧接口"""
        if city:
            self._city = city
        self._cache = {}
        self._cache_ts = 0

    def set_city(self, city: str):
        """设置城市"""
        self._city = city
        self._cache = {}
        self._cache_ts = 0
        self._location_detected = True

    def _detect_location(self) -> str:
        """通过 IP 定位用户城市"""
        try:
            # 使用免费 IP 定位服务
            resp = httpx.get("https://ipapi.co/json/", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                city = data.get("city", "")
                if city:
                    print(f"[Weather] IP 定位成功: {city}")
                    return city
        except Exception as e:
            print(f"[Weather] IP 定位失败: {e}")

        # 备用定位服务
        try:
            resp = httpx.get("http://ip-api.com/json/?lang=zh-CN", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                city = data.get("city", "")
                if city:
                    print(f"[Weather] 备用定位成功: {city}")
                    return city
        except Exception as e:
            print(f"[Weather] 备用定位也失败: {e}")

        return "Changsha"  # 默认长沙

    def _get_city(self) -> str:
        """获取城市名，如果未设置则自动定位"""
        if self._city:
            return self._city
        if not self._location_detected:
            self._city = self._detect_location()
            self._location_detected = True
        return self._city or "Beijing"

    def _get_cached(self) -> Optional[dict]:
        if self._cache and (time.time() - self._cache_ts) < CACHE_TTL:
            return self._cache
        return None

    def _get_stale_now(self) -> Optional[dict]:
        cached_now = self._cache.get("now")
        if not cached_now:
            return None
        stale = dict(cached_now)
        stale["_stale"] = True
        return stale

    @staticmethod
    def _read_weather_text(condition: dict) -> str:
        if condition.get("lang_zh"):
            return condition["lang_zh"][0].get("value", "")
        weather_desc = condition.get("weatherDesc") or []
        if weather_desc:
            return weather_desc[0].get("value", "")
        return ""

    @staticmethod
    def _pick_forecast_condition(day: dict) -> dict:
        hourly = day.get("hourly") or []
        if not hourly:
            return {}
        if len(hourly) > 4:
            return hourly[4]
        return hourly[-1]

    @staticmethod
    def _translate_weather_text(weather_text: str) -> str:
        weather_text = (weather_text or "").strip()
        if not weather_text:
            return ""

        weather_text_lower = weather_text.lower()
        for en, cn in WEATHER_CN_MAP.items():
            if en.lower() == weather_text_lower:
                return cn

        for en, cn in sorted(WEATHER_CN_MAP.items(), key=lambda item: len(item[0]), reverse=True):
            if en.lower() in weather_text_lower:
                return cn

        return weather_text

    def now(self) -> dict:
        """获取当前天气。失败返回上次缓存或默认值。"""
        cached = self._get_cached()
        if cached and "now" in cached:
            return cached["now"]

        city = self._get_city()
        try:
            # wttr.in JSON 接口
            url = f"{API_BASE}/{city}?format=j1"
            # 注：wttr.in 不识别 Accept-Language，中文描述由 WEATHER_CN_MAP 映射提供
            resp = httpx.get(url, timeout=5.0)
            resp.raise_for_status()
            data = resp.json()

            # 解析当前天气
            current = data.get("current_condition", [{}])[0]
            
            weather_text = self._translate_weather_text(self._read_weather_text(current))
            
            result = {
                "temp": current.get("temp_C", "--"),
                "text": weather_text,
                "humidity": current.get("humidity", ""),
                "wind_speed": current.get("windspeedKmph", ""),
                "icon": self._get_icon(current.get("weatherDesc", [{}])[0].get("value", ""), weather_text),
                "city": city,
            }

            # 缓存
            self._cache["now"] = result
            self._cache_ts = time.time()
            return result

        except Exception as e:
            print(f"[Weather] 获取天气失败: {e}")
            stale = self._get_stale_now()
            if stale:
                return stale
            return {"temp": "--", "text": "天气暂不可用", "icon": "⛅", "city": city, "error": str(e)}

    def forecast(self, days: int = 3) -> dict:
        """获取多日预报。"""
        cached = self._get_cached()
        if cached and "forecast" in cached:
            return cached["forecast"]

        city = self._get_city()
        try:
            url = f"{API_BASE}/{city}?format=j1"
            # 注：wttr.in 不识别 Accept-Language，中文描述由 WEATHER_CN_MAP 映射提供
            resp = httpx.get(url, timeout=8.0)
            resp.raise_for_status()
            data = resp.json()

            forecast_list = []
            for day in data.get("weather", [])[:days]:
                noon_weather = self._pick_forecast_condition(day)
                forecast_list.append({
                    "date": day.get("date", ""),
                    "max_temp": day.get("maxtempC", ""),
                    "min_temp": day.get("mintempC", ""),
                    "text": self._translate_weather_text(self._read_weather_text(noon_weather)),
                })

            result = {"daily": forecast_list}
            self._cache["forecast"] = result
            self._cache_ts = time.time()
            return result

        except Exception as e:
            print(f"[Weather] 获取预报失败: {e}")
            if cached and "forecast" in cached:
                cached["forecast"]["_stale"] = True
                return cached["forecast"]
            return {"daily": []}

    @staticmethod
    def _get_icon(weather_desc: str, cn_text: str = "") -> str:
        """根据天气描述返回图标，优先用中文匹配"""
        # 先用中文匹配
        cn_icon_map = {
            "晴": "☀️",
            "多云": "⛅",
            "阴": "☁️",
            "雾": "🌫️",
            "小雨": "🌧️",
            "阵雨": "🌦️",
            "中雨": "🌧️",
            "大雨": "🌧️",
            "雷阵雨": "⛈️",
            "小雪": "🌨️",
            "中雪": "❄️",
            "大雪": "❄️",
        }
        
        if cn_text:
            for cn, icon in cn_icon_map.items():
                if cn in cn_text:
                    return icon
        
        # 再用英文匹配
        en_icon_map = {
            "Sunny": "☀️",
            "Clear": "🌙",
            "Partly cloudy": "⛅",
            "Cloudy": "☁️",
            "Overcast": "☁️",
            "Mist": "🌫️",
            "Fog": "🌫️",
            "Light Rain": "🌧️",
            "Patchy rain": "🌦️",
            "Moderate rain": "🌧️",
            "Heavy rain": "🌧️",
            "Thunder": "⛈️",
        }
        
        weather_desc_lower = weather_desc.lower()
        for en, icon in en_icon_map.items():
            if en.lower() in weather_desc_lower:
                return icon
        
        return "🌤️"
