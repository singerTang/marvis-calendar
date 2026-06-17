"""Marvis Calendar — 系统托盘

提供托盘图标：单击或菜单切换窗口显示/隐藏，菜单退出。
托盘实例同时供 ReminderService 复用以弹出气泡通知。
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QStyle
from PySide6.QtGui import QAction


class Shell:
    """系统托盘管理。"""

    def __init__(self, app, window=None):
        self._app = app
        self._window = window
        self._tray: QSystemTrayIcon | None = None
        self._init_tray()

    @property
    def tray(self) -> QSystemTrayIcon | None:
        return self._tray

    def set_window(self, window):
        self._window = window

    def _init_tray(self):
        """初始化托盘图标与菜单。"""
        self._tray = QSystemTrayIcon()
        # 复用应用图标；缺失时回退系统标准图标，确保托盘可见
        icon = self._app.windowIcon()
        if icon.isNull():
            icon = self._app.style().standardIcon(QStyle.SP_ComputerIcon)
        self._tray.setIcon(icon)
        self._tray.setToolTip("鑫哥日历")

        menu = QMenu()
        show_action = QAction("显示/隐藏", menu)
        show_action.triggered.connect(self._toggle)
        menu.addAction(show_action)

        menu.addSeparator()
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self._app.quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    def _on_activated(self, reason):
        """单击托盘图标切换窗口显示。"""
        if reason == QSystemTrayIcon.Trigger:
            self._toggle()

    def _toggle(self):
        """切换窗口显示/隐藏。"""
        if self._window is None:
            return
        visible = self._window.property("visible")
        self._window.setProperty("visible", not visible)
