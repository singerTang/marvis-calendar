"""Marvis Calendar — 主窗口与应用入口

简洁版：使用 Qt 原生无边框 + 透明窗口。
"""

import sys
import ctypes
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QSurfaceFormat, QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine

from src.models.database import Database
from src.services.calendar import CalendarService
from src.services.almanac import AlmanacService
from src.services.weather import WeatherService
from src.bridge import Bridge
from src.shell import Shell
from src.services.reminder import ReminderService


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
    qwin.setFlags(Qt.FramelessWindowHint | Qt.Window)
    qwin.show()

    # 系统托盘
    app.setQuitOnLastWindowClosed(False)
    shell = Shell(app, qwin)
    reminder = ReminderService(shell.tray)
    reminder.schedule_upcoming(db)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
