"""Marvis Calendar — QML 桥接层

作者: singerTang

将后端 service / database 以 @Slot 形式暴露给 QML 调用。
返回的 dict / list 由 PySide6 自动转换为 QML 的 JS 对象 / 数组，
QML 侧通过 bridge.xxx() 直接取真实数据，替代此前的硬编码占位。
"""

import re
import threading
from datetime import date, datetime, timedelta

from PySide6.QtCore import QObject, Slot, Signal
from PySide6.QtQml import QJSValue

# 非全天日程的时分格式校验：00:00 ~ 23:59
_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class Bridge(QObject):
    """QML 与 Python 后端的数据桥。"""

    # 天气数据异步返回信号
    weatherReady = Signal(dict)

    # 日程变更信号：参数为受影响日期 "YYYY-MM-DD"，供 QML 监听刷新
    eventsChanged = Signal(str)

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

    @Slot(str, result="QVariant")
    def event_for_edit(self, eid) -> dict:
        """返回供 EventDialog 回填的事件结构（字段对齐表单），不存在则返回 None。"""
        e = self._db.get_event(eid)
        if not e:
            return None
        all_day = bool(e.get("all_day"))
        reminder = e.get("reminder_minutes")
        return {
            "id": e["id"],
            "title": e["title"],
            "date": e["start_time"][:10],
            "all_day": all_day,
            "start_hhmm": "" if all_day else Bridge._hhmm(e["start_time"]),
            "end_hhmm": "" if all_day or not e.get("end_time") else Bridge._hhmm(e["end_time"]),
            "notes": e.get("notes") or "",
            "color": e.get("color") or "#5e8cf0",
            "reminder_minutes": -1 if reminder is None else int(reminder),
        }

    # ─── 日程写入 ─────────────────────────────────────────────────────────

    @Slot("QVariant", result="QVariant")
    def add_event(self, data) -> dict:
        """新增日程。data 为 QML 传入的 dict，返回 {ok,error,event}。"""
        data = self._to_dict(data)
        params, error = self._parse_event(data)
        if error:
            return {"ok": False, "error": error, "event": None}
        try:
            event = self._db.add_event(**params)
        except Exception as exc:
            return {"ok": False, "error": str(exc), "event": None}
        if not event:
            return {"ok": False, "error": "保存失败", "event": None}
        self.eventsChanged.emit(data["date"])
        return {"ok": True, "error": "", "event": event}

    @Slot(str, "QVariant", result="QVariant")
    def update_event(self, eid, data) -> dict:
        """更新日程。data 契约同 add_event，返回 {ok,error,event}。"""
        data = self._to_dict(data)
        params, error = self._parse_event(data)
        if error:
            return {"ok": False, "error": error, "event": None}
        if not self._db.get_event(eid):
            return {"ok": False, "error": "日程不存在", "event": None}
        try:
            event = self._db.update_event(eid, **params)
        except Exception as exc:
            return {"ok": False, "error": str(exc), "event": None}
        if not event:
            return {"ok": False, "error": "更新失败", "event": None}
        self.eventsChanged.emit(data["date"])
        return {"ok": True, "error": "", "event": event}

    @Slot(str, result=bool)
    def delete_event(self, eid) -> bool:
        """删除日程；先取受影响日期再删，成功后发射 eventsChanged。"""
        existing = self._db.get_event(eid)
        if not existing:
            return True  # 幂等：不存在视为已删除，不发信号
        try:
            self._db.delete_event(eid)
        except Exception:
            return False
        self.eventsChanged.emit(existing["start_time"][:10])
        return True

    # ─── 日程写入辅助 ─────────────────────────────────────────────────────

    @staticmethod
    def _to_dict(data):
        """QML 传入的对象可能是 QJSValue，统一转为 Python dict 再处理。"""
        if isinstance(data, QJSValue):
            return data.toVariant()
        return data

    @staticmethod
    def _build_times(data):
        """组装并校验起止时间，返回 (start_iso, end_iso, error)。

        - 全天：start = date+"T00:00:00"，end = None
        - 非全天：校验 HH:MM 格式，要求 end >= start
        校验失败时 start/end 为 None，error 为中文错误信息。
        """
        date_str = data.get("date")
        if not date_str:
            return None, None, "缺少日期"
        if data.get("all_day"):
            return date_str + "T00:00:00", None, ""
        start_hhmm = data.get("start_hhmm") or ""
        end_hhmm = data.get("end_hhmm") or ""
        if not _HHMM_RE.match(start_hhmm):
            return None, None, "开始时间格式不正确"
        if not _HHMM_RE.match(end_hhmm):
            return None, None, "结束时间格式不正确"
        if end_hhmm < start_hhmm:
            return None, None, "结束时间不能早于开始时间"
        start_iso = date_str + "T" + start_hhmm + ":00"
        end_iso = date_str + "T" + end_hhmm + ":00"
        return start_iso, end_iso, ""

    @staticmethod
    def _parse_event(data):
        """将 QML data 解析为 database 入参，返回 (params, error)。

        校验标题非空、时间合法；处理 reminder_minutes(-1→None) 与 color 回退。
        校验失败时 params 为 None，error 为中文错误信息。
        """
        title = (data.get("title") or "").strip()
        if not title:
            return None, "标题不能为空"

        start_iso, end_iso, error = Bridge._build_times(data)
        if error:
            return None, error

        reminder = data.get("reminder_minutes")
        reminder_minutes = None if reminder is None or reminder == -1 else int(reminder)
        color = data.get("color") or "#5e8cf0"

        params = {
            "title": title,
            "start_time": start_iso,
            "end_time": end_iso,
            "all_day": 1 if data.get("all_day") else 0,
            "reminder_minutes": reminder_minutes,
            "notes": data.get("notes") or None,
            "color": color,
        }
        return params, ""

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
