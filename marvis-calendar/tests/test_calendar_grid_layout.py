"""月历选中态布局回归测试。

作者：singerTang <109527086+singerTang@users.noreply.github.com>
"""

import re
import unittest
from pathlib import Path


class CalendarGridLayoutTest(unittest.TestCase):
    def _read_qml(self, file_name):
        return (
            Path(__file__).resolve().parents[1]
            / "src"
            / "qml"
            / file_name
        ).read_text(encoding="utf-8")

    def test_selected_circle_wraps_day_and_lunar_text(self):
        qml = self._read_qml("CalendarGrid.qml")

        select_circle = re.search(
            r"Rectangle\s*\{\s*id:\s*selectCircle(?P<body>.*?)visible:",
            qml,
            re.S,
        )

        self.assertIsNotNone(select_circle, "应存在选中圆圈配置")
        self.assertIn("anchors.centerIn: selectedDateContent", select_circle.group("body"))
        self.assertIn("id: selectedDateContent", qml)
        self.assertIn("id: lunarText", qml)
        self.assertIn("modelData.isToday || isSelected || isHovered", qml)
        self.assertIn("if (modelData.isToday) return root.accent", qml)
        self.assertIn("if (isSelected) return \"transparent\"", qml)
        self.assertIn("if (isHovered) return Qt.rgba", qml)
        self.assertIn("if (isSelected && !modelData.isToday) return 2", qml)

    def test_hover_keeps_lunar_text_visible_and_still(self):
        qml = self._read_qml("CalendarGrid.qml")

        self.assertIn("anchors.topMargin: 6", qml)
        self.assertIn('visible: text !== ""', qml)
        self.assertNotIn("isHovered && modelData.isCurrentMonth", qml)

    def test_hover_exit_does_not_clear_new_hovered_date(self):
        qml = self._read_qml("CalendarGrid.qml")

        self.assertIn("if (root.hoveredDate === modelData.date)", qml)
        self.assertIn('root.hoveredDate = ""', qml)

    def test_calendar_grid_receives_selected_date_from_window(self):
        qml = self._read_qml("main.qml")

        self.assertIn("function dateKey(d)", qml)
        self.assertIn("selectedDate: root.dateKey(root.selectedDate)", qml)

    def test_temperature_uses_celsius_symbol(self):
        qml = self._read_qml("DetailPane.qml")

        self.assertIn('+ "℃"', qml)

    def test_left_panel_owns_time_date_lunar_and_weather_header(self):
        detail_qml = self._read_qml("DetailPane.qml")
        main_qml = self._read_qml("main.qml")

        self.assertIn("property date selectedDate", detail_qml)
        self.assertIn("property var weatherData", detail_qml)
        self.assertIn("id: currentTimeText", detail_qml)
        self.assertIn("id: weatherHeader", detail_qml)
        self.assertIn("selectedDate: root.selectedDate", main_qml)
        self.assertIn("weatherData: root.weatherData", main_qml)

    def test_calendar_grid_owns_month_switcher_above_week_header(self):
        qml = self._read_qml("CalendarGrid.qml")

        month_header_index = qml.index("id: monthHeader")
        week_header_index = qml.index("// 星期头")
        self.assertLess(month_header_index, week_header_index)
        self.assertIn("calendarGridMonthLabel", qml)
        self.assertIn("onClicked: root.prevMonth()", qml)
        self.assertIn("onClicked: root.nextMonth()", qml)

    def test_main_title_bar_no_longer_contains_calendar_or_weather_business_info(self):
        qml = self._read_qml("main.qml")

        title_bar_start = qml.index("id: titleBar")
        title_bar_end = qml.index("// ─── 双卡片区域")
        title_bar = qml[title_bar_start:title_bar_end]
        self.assertNotIn("weatherData", title_bar)
        self.assertNotIn("calendarGrid.currentYear", title_bar)

    def test_window_is_frameless_and_outer_shell_has_no_border(self):
        qml = self._read_qml("main.qml")

        self.assertIn("flags: Qt.FramelessWindowHint | Qt.Window", qml)
        self.assertIn("border.width: 0", qml)
        self.assertIn("antialiasing: true", qml)

    def test_left_card_and_weather_header_have_enough_width(self):
        main_qml = self._read_qml("main.qml")
        detail_qml = self._read_qml("DetailPane.qml")

        self.assertIn("Layout.preferredWidth: 0.85", main_qml)
        self.assertIn("Layout.minimumWidth: 68", detail_qml)
        self.assertIn("width: 68", detail_qml)


if __name__ == "__main__":
    unittest.main()
