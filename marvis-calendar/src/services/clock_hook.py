"""Marvis Calendar — 任务栏时钟点击钩子

作者: singerTang

通过 Windows 全局低级鼠标钩子（WH_MOUSE_LL）拦截任务栏右下角时钟区域的
左键点击，命中后发出 clockClicked 信号供上层切换日历显示，并吞掉该次点击
以阻止系统自带日历面板弹出。

设计要点：
- 低级钩子无需注入 DLL，可在本进程 Qt 主线程消息循环中工作。
- 时钟命中区域：优先用 Shell_TrayWnd（任务栏整体）矩形的最右侧一段宽度，
  自适应任务栏位置与高度；找不到任务栏时回退到主屏右下角矩形近似。
- 仅在 Windows 生效；其他平台 install/uninstall 为空操作。
"""

import sys
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QObject, QPoint, QTimer, Signal

# 低级鼠标钩子与消息常量
_WH_MOUSE_LL = 14
_WM_LBUTTONDOWN = 0x0201
_WM_LBUTTONUP = 0x0202
_WM_RBUTTONDOWN = 0x0204
_WM_RBUTTONUP = 0x0205

# 任务栏右侧时钟命中区域宽度（物理像素）。覆盖时间、日期和通知按钮，不覆盖左侧托盘图标。
_CLOCK_WIDTH = 158


class _POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class _MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", _POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


# 钩子回调签名：LRESULT CALLBACK(int nCode, WPARAM wParam, LPARAM lParam)
_CALLBACK_FACTORY = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)
_LRESULT = ctypes.c_ssize_t
_HHOOK = getattr(wintypes, "HHOOK", wintypes.HANDLE)
_HOOKPROC = _CALLBACK_FACTORY(
    _LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)


class ClockHook(QObject):
    """任务栏时钟点击钩子：命中即发信号并吞掉点击。"""

    clockClicked = Signal()
    clockRightClicked = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hook = None
        # 必须持有回调引用，否则会被 GC 回收导致钩子崩溃
        self._proc = None
        self._user32 = None
        self._is_windows = sys.platform.startswith("win")
        self._suppress_left_up = False
        self._suppress_right_up = False
        self._last_error = 0

    def install(self) -> bool:
        """安装全局鼠标钩子；成功返回 True。"""
        if not self._is_windows or self._hook is not None:
            return False

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            _HOOKPROC,
            wintypes.HINSTANCE,
            wintypes.DWORD,
        ]
        user32.SetWindowsHookExW.restype = _HHOOK
        user32.UnhookWindowsHookEx.argtypes = [_HHOOK]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        user32.CallNextHookEx.argtypes = [
            _HHOOK,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.CallNextHookEx.restype = _LRESULT
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE

        self._proc = _HOOKPROC(self._on_mouse)
        hmod = kernel32.GetModuleHandleW(None)
        self._hook = user32.SetWindowsHookExW(
            _WH_MOUSE_LL, self._proc, hmod, 0
        )
        if self._hook:
            self._last_error = 0
            self._user32 = user32
            return True

        self._last_error = ctypes.get_last_error()
        self._proc = None
        self._user32 = None
        return False

    def uninstall(self):
        """卸载钩子，释放回调引用。"""
        if self._hook is not None:
            user32 = self._user32 or ctypes.WinDLL("user32", use_last_error=True)
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
        self._proc = None
        self._user32 = None

    def last_error(self) -> int:
        """返回最近一次安装钩子失败的 Win32 错误码。"""
        return int(self._last_error)

    # ─── 内部 ─────────────────────────────────────────────────────────

    def _on_mouse(self, n_code, w_param, l_param):
        """钩子回调：命中时钟区域则发信号并吞事件。"""
        if n_code >= 0 and w_param in (
            _WM_LBUTTONDOWN,
            _WM_LBUTTONUP,
            _WM_RBUTTONDOWN,
            _WM_RBUTTONUP,
        ):
            info = ctypes.cast(l_param, ctypes.POINTER(_MSLLHOOKSTRUCT)).contents
            hit_clock = self._hit_clock(info.pt.x, info.pt.y)

            if w_param == _WM_LBUTTONDOWN and hit_clock:
                self._suppress_left_up = True
                QTimer.singleShot(0, self.clockClicked.emit)
                return 1

            if w_param == _WM_LBUTTONUP and self._suppress_left_up:
                self._suppress_left_up = False
                return 1

            if w_param == _WM_RBUTTONDOWN and hit_clock:
                self._suppress_right_up = True
                return 1

            if w_param == _WM_RBUTTONUP and self._suppress_right_up:
                self._suppress_right_up = False
                x, y = info.pt.x, info.pt.y
                QTimer.singleShot(
                    0, lambda pos_x=x, pos_y=y: self.clockRightClicked.emit(pos_x, pos_y)
                )
                return 1
        user32 = self._user32 or ctypes.windll.user32
        return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

    def menu_position(self, x: int, y: int, menu_size):
        """把右键菜单放到点击点上方，避免压住任务栏右下角。"""
        rect = self._tray_rect()
        menu_width = int(menu_size.width())
        menu_height = int(menu_size.height())
        if rect is None:
            return QPoint(int(x), int(y) - menu_height)

        left, top, right, _bottom = rect
        menu_x = max(left, min(int(x), right - menu_width))
        menu_y = max(0, top - menu_height - 4)
        return QPoint(menu_x, menu_y)

    def _hit_clock(self, x: int, y: int) -> bool:
        """判断屏幕坐标 (x, y) 是否落在任务栏右侧时钟区域。"""
        rect = self._tray_rect()
        if rect is None:
            return False
        left, top, right, bottom = rect
        taskbar_height = max(1, bottom - top)
        clock_width = max(_CLOCK_WIDTH, int(taskbar_height * 3.2))
        clock_left = right - clock_width
        return clock_left <= x <= right and top <= y <= bottom

    def _tray_rect(self):
        """返回任务栏矩形 (left, top, right, bottom)，失败回退主屏底部条。"""
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        hwnd = user32.FindWindowW("Shell_TrayWnd", None)
        if hwnd:
            r = wintypes.RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(r)):
                return r.left, r.top, r.right, r.bottom

        # 回退：主屏右下角，取屏幕高度推断一条任务栏高度的底部条带
        sw = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        sh = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        taskbar_h = 48
        return 0, sh - taskbar_h, sw, sh
