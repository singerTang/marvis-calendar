"""日历窗口显示位置与切换控制。

作者：singerTang <109527086+singerTang@users.noreply.github.com>
"""

from PySide6.QtGui import QGuiApplication


def _geometry_value(geometry, name: str) -> int:
    value = getattr(geometry, name)
    return int(value() if callable(value) else value)


def bottom_right_position(geometry, window_width: int, window_height: int, margin: int = 8):
    """按屏幕可用区域计算窗口右下角坐标。"""
    left = _geometry_value(geometry, "x")
    top = _geometry_value(geometry, "y")
    right = left + _geometry_value(geometry, "width")
    bottom = top + _geometry_value(geometry, "height")

    x = max(left + margin, right - int(window_width) - margin)
    y = max(top + margin, bottom - int(window_height) - margin)
    return x, y


class ClockCalendarWindowController:
    """控制任务栏时钟触发的日历窗口显示、隐藏和固定定位。"""

    def __init__(self, window, margin: int = 8, screen_provider=None):
        self._window = window
        self._margin = margin
        self._screen_provider = screen_provider or QGuiApplication.primaryScreen

    def toggle(self):
        """隐藏则固定到右下角后显示，显示则隐藏。"""
        if self._is_visible():
            self._window.setProperty("visible", False)
            return

        self.move_to_bottom_right()
        self._window.setProperty("visible", True)
        self._raise_and_activate()

    def move_to_bottom_right(self):
        geometry = self._available_geometry()
        if geometry is None:
            return

        x, y = bottom_right_position(
            geometry,
            self._window.width(),
            self._window.height(),
            self._margin,
        )
        self._window.setPosition(x, y)

    def _is_visible(self) -> bool:
        return bool(self._window.property("visible"))

    def _available_geometry(self):
        screen = self._window.screen()
        if screen is None:
            screen = self._screen_provider()
        if screen is None:
            return None
        return screen.availableGeometry()

    def _raise_and_activate(self):
        raise_window = getattr(self._window, "raise_", None)
        if callable(raise_window):
            raise_window()

        request_activate = getattr(self._window, "requestActivate", None)
        if callable(request_activate):
            request_activate()
