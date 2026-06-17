"""Marvis Calendar — 日历服务

使用 lunar-python 库（覆盖 1900-2100 农历 + 节气 + 节假日）。
只保留大型节日，不显示小节日。
"""

from datetime import date, timedelta
from typing import Optional

from lunar_python import Lunar, Solar


class CalendarService:
    """公历/农历/节气/节假日查询。"""

    # 只保留大型节日（公历）
    SOLAR_FESTIVALS = {
        (1, 1): "元旦",
        (5, 1): "劳动节",
        (6, 1): "儿童节",
        (10, 1): "国庆节",
    }

    # 只保留大型节日（农历）
    LUNAR_FESTIVALS = {
        (1, 1): "春节",
        (1, 15): "元宵",
        (5, 5): "端午",
        (8, 15): "中秋",
        (9, 9): "重阳",
        (12, 30): "除夕",
    }

    # 节假日假期（需要标"休"的日期）
    # 这里用 (年, 月, 日) 的集合来标记
    # 实际使用时应该从网络获取最新的放假安排
    HOLIDAY_VACATIONS = {
        # 2026年节假日假期（示例）
        # 元旦
        (2026, 1, 1),
        # 春节
        (2026, 1, 26), (2026, 1, 27), (2026, 1, 28), (2026, 1, 29),
        (2026, 1, 30), (2026, 1, 31), (2026, 2, 1),
        # 清明
        (2026, 4, 4), (2026, 4, 5), (2026, 4, 6),
        # 劳动节
        (2026, 5, 1), (2026, 5, 2), (2026, 5, 3), (2026, 5, 4), (2026, 5, 5),
        # 端午
        (2026, 6, 19), (2026, 6, 20), (2026, 6, 21),
        # 中秋+国庆
        (2026, 10, 1), (2026, 10, 2), (2026, 10, 3), (2026, 10, 4),
        (2026, 10, 5), (2026, 10, 6), (2026, 10, 7),
    }

    # ─── 公历信息 ───────────────────────────────────────────────────────

    @staticmethod
    def _to_solar(d: date) -> Solar:
        """将 datetime.date 转为 lunar-python Solar 对象。"""
        return Solar.fromYmd(d.year, d.month, d.day)

    @staticmethod
    def get_month_days(year: int, month: int) -> list[date]:
        """返回某月所有日期列表（含前后月补齐到 42 格）。"""
        first = date(year, month, 1)
        start = first - timedelta(days=first.weekday())
        return [start + timedelta(days=i) for i in range(42)]

    @staticmethod
    def get_week_days(target: date) -> list[date]:
        """返回 target 所在周的日期（周一到周日）。"""
        monday = target - timedelta(days=target.weekday())
        return [monday + timedelta(days=i) for i in range(7)]

    # ─── 农历信息 ───────────────────────────────────────────────────────

    def lunar_info(self, d: date) -> dict:
        """返回指定日期的农历摘要。"""
        solar = self._to_solar(d)
        lunar = solar.getLunar()
        return {
            "year": lunar.getYear(),
            "month": lunar.getMonth(),
            "day": lunar.getDay(),
            "year_cn": lunar.getYearInChinese(),
            "month_cn": lunar.getMonthInChinese(),
            "day_cn": lunar.getDayInChinese(),
            "is_leap_month": lunar.getMonth() < 0,
            "zodiac": lunar.getYearShengXiao(),
            "ganzhi_year": lunar.getYearInGanZhi(),
            "ganzhi_month": lunar.getMonthInGanZhi(),
            "ganzhi_day": lunar.getDayInGanZhi(),
        }

    # ─── 节气 ───────────────────────────────────────────────────────────

    def solar_term(self, d: date) -> Optional[str]:
        """返回节气名，非节气日返回 None。"""
        solar = self._to_solar(d)
        term = solar.getLunar().getJieQi()
        return term if term else None

    def next_solar_term(self, d: date) -> dict:
        """返回 d 之后的下一个节气及距今天数。"""
        solar = self._to_solar(d)
        next_term = solar.getLunar().getNextJieQi()
        if next_term:
            return {"name": next_term.getName(), "date": next_term.getSolar().toYmd()}
        return {}

    # ─── 节假日 ─────────────────────────────────────────────────────────

    def get_festival_name(self, d: date) -> str:
        """返回大型节日名称，无节日返回空字符串。"""
        solar = self._to_solar(d)
        lunar = solar.getLunar()

        # 检查公历节日
        solar_key = (d.month, d.day)
        if solar_key in self.SOLAR_FESTIVALS:
            return self.SOLAR_FESTIVALS[solar_key]

        # 检查农历节日
        lunar_key = (abs(lunar.getMonth()), lunar.getDay())
        if lunar_key in self.LUNAR_FESTIVALS:
            return self.LUNAR_FESTIVALS[lunar_key]

        return ""

    def is_holiday_vacation(self, d: date) -> bool:
        """判断是否为节假日假期（需要标"休"）"""
        return (d.year, d.month, d.day) in self.HOLIDAY_VACATIONS

    def is_workday(self, d: date) -> bool:
        """判断是否为工作日。周末默认非工作日，节假日默认非工作日。"""
        if d.weekday() >= 5:
            return False
        if self.is_holiday_vacation(d):
            return False
        return True

    # ─── 聚合 ───────────────────────────────────────────────────────────

    def day_info(self, d: date) -> dict:
        """单日完整信息聚合。"""
        lunar = self.lunar_info(d)
        return {
            "date": d.isoformat(),
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "weekday": d.weekday(),       # 0=周一
            "weekday_cn": ["一","二","三","四","五","六","日"][d.weekday()],
            "lunar": lunar,
            "solar_term": self.solar_term(d),
            "holiday": self.get_festival_name(d) or None,
            "festival": self.get_festival_name(d),
            "is_weekend": d.weekday() >= 5,
            "is_today": d == date.today(),
            "is_workday": self.is_workday(d),
            "is_holiday_vacation": self.is_holiday_vacation(d),
        }
