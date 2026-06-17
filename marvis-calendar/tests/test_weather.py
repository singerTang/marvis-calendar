"""天气服务回归测试。

作者：singerTang <109527086+singerTang@users.noreply.github.com>
"""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


def load_weather_module():
    module_path = Path(__file__).resolve().parents[1] / "src" / "services" / "weather.py"
    spec = importlib.util.spec_from_file_location("weather", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, data):
        self._data = data
        self.status_code = 200

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


class WeatherTranslationTest(unittest.TestCase):
    def setUp(self):
        self.weather_module = load_weather_module()

    def test_now_translates_drizzle_to_chinese(self):
        service = self.weather_module.WeatherService()
        service.set_city("Beijing")
        payload = {
            "current_condition": [
                {
                    "temp_C": "26",
                    "humidity": "80",
                    "windspeedKmph": "8",
                    "weatherDesc": [{"value": "Light drizzle"}],
                }
            ]
        }

        with patch.object(self.weather_module.httpx, "get", return_value=FakeResponse(payload)):
            result = service.now()

        self.assertEqual(result["text"], "小雨")

    def test_now_translates_smoky_haze_to_chinese(self):
        service = self.weather_module.WeatherService()
        service.set_city("Beijing")
        payload = {
            "current_condition": [
                {
                    "temp_C": "26",
                    "humidity": "80",
                    "windspeedKmph": "8",
                    "weatherDesc": [{"value": "Smoky haze"}],
                }
            ]
        }

        with patch.object(self.weather_module.httpx, "get", return_value=FakeResponse(payload)):
            result = service.now()

        self.assertEqual(result["text"], "霾")

    def test_forecast_translates_english_when_chinese_missing(self):
        service = self.weather_module.WeatherService()
        service.set_city("Beijing")
        payload = {
            "weather": [
                {
                    "date": "2026-06-17",
                    "maxtempC": "28",
                    "mintempC": "20",
                    "hourly": [
                        {},
                        {},
                        {},
                        {},
                        {"weatherDesc": [{"value": "Light drizzle"}]},
                    ],
                }
            ]
        }

        with patch.object(self.weather_module.httpx, "get", return_value=FakeResponse(payload)):
            result = service.forecast()

        self.assertEqual(
            result["daily"],
            [
                {
                    "date": "2026-06-17",
                    "max_temp": "28",
                    "min_temp": "20",
                    "text": "小雨",
                }
            ],
        )

    def test_forecast_uses_available_hourly_when_no_noon_slot(self):
        service = self.weather_module.WeatherService()
        service.set_city("Beijing")
        payload = {
            "weather": [
                {
                    "date": "2026-06-17",
                    "maxtempC": "28",
                    "mintempC": "20",
                    "hourly": [{"weatherDesc": [{"value": "Light drizzle"}]}],
                }
            ]
        }

        with patch.object(self.weather_module.httpx, "get", return_value=FakeResponse(payload)):
            result = service.forecast()

        self.assertEqual(
            result["daily"],
            [
                {
                    "date": "2026-06-17",
                    "max_temp": "28",
                    "min_temp": "20",
                    "text": "小雨",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
