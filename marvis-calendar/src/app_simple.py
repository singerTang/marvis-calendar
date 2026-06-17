"""Marvis Calendar — 简化测试入口（无 Acrylic）

用于调试白屏问题。
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine

from src.models.database import Database
from src.services.calendar import CalendarService
from src.services.almanac import AlmanacService
from src.services.weather import WeatherService
from src.bridge import Bridge


def _db_path() -> Path:
    base = Path.home() / "AppData" / "Roaming" / "MarvisCalendar"
    base.mkdir(parents=True, exist_ok=True)
    return base / "marvis.db"


def main():
    # 开启 alpha buffer
    fmt = QSurfaceFormat()
    fmt.setAlphaBufferSize(8)
    QSurfaceFormat.setDefaultFormat(fmt)

    # 关键：启用透明窗口
    app = QApplication(sys.argv)
    app.setApplicationName("Marvis Calendar")
    app.setOrganizationName("Marvis")

    db = Database(_db_path())
    db.initialize()

    # 统一通过 Bridge(QObject) 暴露后端能力给 QML
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

    # 关键：设置窗口为无边框（透明背景在 QML 中已设置 color: "transparent"）
    qwin.setFlags(Qt.FramelessWindowHint | Qt.Window)

    print("SUCCESS: Window loaded!")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
