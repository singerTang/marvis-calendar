"""Marvis Calendar — QML 桥接层

作者: singerTang

将后端 service / database 以 @Slot 形式暴露给 QML 调用。
返回的 dict / list 由 PySide6 自动转换为 QML 的 JS 对象 / 数组，
QML 侧通过 bridge.xxx() 直接取真实数据，替代此前的硬编码占位。
"""

import threading
from datetime import date, datetime, timedelta

from PySide6.QtCore import QObject, Slot, Signal


class Bridge(QObject):
    """QML 与 Python 后端的数据桥。"""

    # 天气数据异步返回信号
    weatherReady = Signal(dict)

    def __init__(self, db, calendar, almanac, weather):
        super().__init__()
        self._db = db
        self._cal = calendar
        self._alm = almanac
        self._weather = weather

    # ─── 月历网格 ─────────────────────────────────────────────────────────

    @Slot(int, int, result="QVariant")
    def month_grid(self, year: int, month: int) -> list:
        """返回某月 42 格日期数据（month 为 1-based）。"""
        days = self._cal.get_month_days(year, month)
        events = self._db.get_events_by_range(
            days[0].isoformat(), (days[-1] + timedelta(days=1)).isoformat())
        event_dates = {e["start_time"][:10] for e in events}

        grid = []
        for d in days:
            info = self._cal.day_info(d)
            lunar = info["lunar"]
            # 初一显示"X月"，其余显示农历日
            label = (lunar["month_cn"] + "月") if lunar["day"] == 1 else lunar["day_cn"]
            
            # 获取节日名称（只显示大节日）
            festival = info.get("festival", "")
            
            # 判断是否节假日假期（标"休"）
            is_holiday_vacation = info.get("is_holiday_vacation", False)
            
            grid.append({
                "date": d.isoformat(),
                "day": d.day,
                "lunar": label,
                "festival": festival,
                "solarTerm": info["solar_term"] or "",
                "isCurrentMonth": d.month == month,
                "isToday": info["is_today"],
                "isWeekend": info["is_weekend"],
                "isHolidayVacation": is_holiday_vacation,
                "hasEvent": d.isoformat() in event_dates,
                "month": d.month,
            })
        return grid

    # ─── 单日详情 ─────────────────────────────────────────────────────────

    @Slot(str, result="QVariant")
    def day_detail(self, date_str: str) -> dict:
        """返回单日农历、宜忌、日程、下一节气。"""
        d = date.fromisoformat(date_str)
        info = self._cal.day_info(d)
        events = [self._format_event(e) for e in self._db.get_events_by_date(date_str)]
        return {
            "lunar": info["lunar"],
            "almanac": self._alm.daily_almanac_compact(d),
            "events": events,
            "nextTerm": self._cal.next_solar_term(d),
            "holiday": info["holiday"] or {},
        }

    @staticmethod
    def _format_event(e: dict) -> dict:
        if e.get("all_day"):
            time_label = "全天"
        else:
            time_label = Bridge._hhmm(e["start_time"])
            if e.get("end_time"):
                time_label += " - " + Bridge._hhmm(e["end_time"])
        return {
            "id": e["id"],
            "time": time_label,
            "title": e["title"],
            "color": e.get("color") or "#5e8cf0",
        }

    @staticmethod
    def _hhmm(iso_str: str) -> str:
        try:
            return datetime.fromisoformat(iso_str).strftime("%H:%M")
        except ValueError:
            return iso_str

    # ─── 待办 ─────────────────────────────────────────────────────────────

    @Slot(result="QVariant")
    def all_todos(self) -> list:
        return self._db.get_all_todos()

    @Slot(str, bool)
    def toggle_todo(self, todo_id: str, completed: bool):
        self._db.update_todo(todo_id, completed=1 if completed else 0)

    # ─── 天气（异步）──────────────────────────────────────────────────────

    @Slot(result="QVariant")
    def weather_now(self) -> dict:
        """同步接口：返回缓存的天气或加载状态。"""
        if hasattr(self, '_last_weather') and self._last_weather:
            return self._last_weather
        return {"configured": True, "temp": "...", "text": "加载中", "loading": True}

    @Slot()
    def fetch_weather_async(self):
        """异步获取天气，完成后发射 weatherReady 信号。"""
        def _fetch():
            result = self._weather.now()
            result["configured"] = True
            self._last_weather = result
            # 信号会自动回到主线程
            self.weatherReady.emit(result)

        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()

    @Slot(str)
    def configure_weather(self, city: str):
        """设置天气城市。"""
        self._weather.set_city(city)
        self._last_weather = None
        self.fetch_weather_async()
