"""Marvis Calendar — 日程提醒服务

基于 Qt 原生能力实现，不引入第三方库：
- 通知：QSystemTrayIcon.showMessage（系统气泡通知）
- 定时：QTimer 单次触发，到点弹出提醒

由 app 启动时调用 schedule_upcoming 扫描近期带提醒的事件并登记。
"""

from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QSystemTrayIcon

# QTimer 以 int 毫秒计时，约 24.8 天上限；超出则不在本次会话登记
_MAX_DELAY_MS = 20 * 24 * 60 * 60 * 1000


class ReminderService(QObject):
    """系统提醒：托盘气泡通知 + 定时调度。"""

    def __init__(self, tray: QSystemTrayIcon = None):
        super().__init__()
        self._tray = tray
        self._timers: dict[str, QTimer] = {}

    @property
    def enabled(self) -> bool:
        return self._tray is not None

    def set_tray(self, tray: QSystemTrayIcon):
        self._tray = tray

    def notify(self, title: str, message: str):
        """弹出系统气泡通知。"""
        if self._tray is not None:
            self._tray.showMessage(title, message, QSystemTrayIcon.Information, 8000)

    def schedule(self, event_id: str, remind_at: str,
                 title: str = "日程提醒", message: str = ""):
        """在 remind_at（ISO 时间）登记一次提醒。"""
        try:
            target = datetime.fromisoformat(remind_at)
        except ValueError:
            return
        delay_ms = int((target - datetime.now()).total_seconds() * 1000)
        if delay_ms <= 0 or delay_ms > _MAX_DELAY_MS:
            return

        self.cancel(event_id)
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.notify(title, message))
        timer.start(delay_ms)
        self._timers[event_id] = timer

    def cancel(self, event_id: str):
        """取消已登记的提醒。"""
        timer = self._timers.pop(event_id, None)
        if timer is not None:
            timer.stop()
            timer.deleteLater()

    def schedule_upcoming(self, db, within_days: int = 7):
        """扫描未来 within_days 天内带 reminder_minutes 的事件并登记提醒。"""
        now = datetime.now()
        end = (now + timedelta(days=within_days)).isoformat()
        for e in db.get_events_by_range(now.isoformat(), end):
            minutes = e.get("reminder_minutes")
            if not minutes:
                continue
            try:
                start = datetime.fromisoformat(e["start_time"])
            except ValueError:
                continue
            remind_at = (start - timedelta(minutes=minutes)).isoformat()
            self.schedule(e["id"], remind_at, "日程提醒", e["title"])
