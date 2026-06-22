"""Marvis Calendar — 主窗口与应用入口

简洁版：使用 Qt 原生无边框 + 透明窗口。
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QSurfaceFormat, QIcon
from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtQml import QQmlApplicationEngine

from src.models.database import Database
from src.services.calendar import CalendarService
from src.services.almanac import AlmanacService
from src.services.weather import WeatherService
from src.bridge import Bridge
from src.services.reminder import ReminderService
from src.services.clock_hook import ClockHook
from src.window_controller import ClockCalendarWindowController


def _db_path() -> Path:
    base = Path.home() / "AppData" / "Roaming" / "MarvisCalendar"
    base.mkdir(parents=True, exist_ok=True)
    return base / "marvis.db"


def main():
    # 开启 alpha buffer
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    QSurfaceFormat.setDefaultFormat(fmt)

    QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, False)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("鑫哥日历")
    app.setOrganizationName("Marvis")

    # 应用图标（任务栏/窗口/托盘共用）
    icon_path = Path(__file__).parent / "assets" / "app.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    db = Database(_db_path())
    db.initialize()

    # Bridge
    bridge = Bridge(
        db,
        CalendarService(),
        AlmanacService(),
        WeatherService(),
    )
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)

    qml_dir = Path(__file__).parent / "qml"
    engine.load(QUrl.fromLocalFile(str(qml_dir / "main.qml")))

    if not engine.rootObjects():
        print("ERROR: QML failed to load!")
        sys.exit(-1)

    qwin = engine.rootObjects()[0]

    # 使用 Qt 原生无边框 + 透明背景
    qwin.setFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
    clock_controller = ClockCalendarWindowController(qwin)
    clock_controller.move_to_bottom_right()
    # 启动时不弹主窗口；任务栏时间区域由鼠标钩子接管。
    qwin.setProperty("visible", False)

    app.setQuitOnLastWindowClosed(False)
    reminder = ReminderService(None)
    reminder.schedule_upcoming(db)

    clock_hook = ClockHook(app)
    clock_hook.clockClicked.connect(clock_controller.toggle)

    def show_clock_menu(x, y):
        menu = QMenu()
        settings_action = QAction("任务栏时钟设置", menu)
        settings_action.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("ms-settings:taskbar"))
        )
        menu.addAction(settings_action)

        menu.addSeparator()
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        menu.exec(clock_hook.menu_position(x, y, menu.sizeHint()))

    clock_hook.clockRightClicked.connect(show_clock_menu)
    if not clock_hook.install():
        print(f"[ClockHook] 安装失败，Win32 错误码：{clock_hook.last_error()}")

    app.aboutToQuit.connect(clock_hook.uninstall)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
