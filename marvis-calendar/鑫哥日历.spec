# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

excluded_modules = [
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs",
    "PySide6.QtHelp",
    "PySide6.QtLocation",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaQuick",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNfc",
    "PySide6.QtPdf",
    "PySide6.QtPdfQuick",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtPrintSupport",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickParticles",
    "PySide6.QtQuickTimeline",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus",
    "PySide6.QtSerialPort",
    "PySide6.QtSql",
    "PySide6.QtStateMachine",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtVirtualKeyboard",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtWebView",
]

drop_tokens = [
    "/translations/",
    "/qml/qt3d",
    "/qml/qt5compat",
    "/qml/qtcharts",
    "/qml/qtdatavisualization",
    "/qml/qtgraphs",
    "/qml/qtlocation",
    "/qml/qtmultimedia",
    "/qml/qtpositioning",
    "/qml/qtquick3d",
    "/qml/qtremoteobjects",
    "/qml/qtscxml",
    "/qml/qtsensors",
    "/qml/qttest",
    "/qml/qttexttospeech",
    "/qml/qtwebchannel",
    "/qml/qtwebengine",
    "/qml/qtwebsockets",
    "/qml/qtwebview",
    "qt63d",
    "qt6bluetooth",
    "qt6charts",
    "qt6datavisualization",
    "qt6designer",
    "qt6graphs",
    "qt6help",
    "qt6location",
    "qt6multimedia",
    "qt6nfc",
    "qt6pdf",
    "qt6positioning",
    "qt6printsupport",
    "qt6quick3d",
    "qt6quickparticles",
    "qt6quicktimeline",
    "qt6remoteobjects",
    "qt6scxml",
    "qt6sensors",
    "qt6serial",
    "qt6sql",
    "qt6statemachine",
    "qt6test",
    "qt6texttospeech",
    "qt6virtualkeyboard",
    "qt6webchannel",
    "qt6webengine",
    "qt6websockets",
    "qt6webview",
]


def keep_entry(entry):
    name = entry[0].replace("\\", "/").lower()
    if not name.startswith("pyside6/"):
        return True
    return not any(token in name for token in drop_tokens)


datas = [
    ("src/assets", "src/assets"),
    ("src/qml", "src/qml"),
]
binaries = []
hiddenimports = []

tmp_ret = collect_all("lunar_python")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    noarchive=False,
    optimize=0,
)
a.binaries = [entry for entry in a.binaries if keep_entry(entry)]
a.datas = [entry for entry in a.datas if keep_entry(entry)]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="鑫哥日历",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["src\\assets\\app.ico"],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="鑫哥日历",
)
