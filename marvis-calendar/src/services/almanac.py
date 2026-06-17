"""Marvis Calendar — 黄历宜忌服务"""

from datetime import date

from lunar_python import Solar


class AlmanacService:
    """黄历宜忌、冲煞、吉神查询。"""

    def daily_almanac(self, d: date) -> dict:
        """返回指定日期的黄历宜忌。"""
        solar = Solar.fromYmd(d.year, d.month, d.day)
        lunar = solar.getLunar()
        return {
            "yi": lunar.getDayYi() or [],
            "ji": lunar.getDayJi() or [],
            "chong": lunar.getDayChongDesc() or "",
            "sha": lunar.getDaySha() or "",
            "ji_shen": lunar.getDayJiShen() or [],
            "xiong_sha": lunar.getDayXiongSha() or [],
        }

    def daily_almanac_compact(self, d: date) -> dict:
        """精简版，适合面板展示。"""
        solar = Solar.fromYmd(d.year, d.month, d.day)
        lunar = solar.getLunar()
        yi = lunar.getDayYi() or []
        ji = lunar.getDayJi() or []
        return {
            "yi": yi[:4] if yi else [],
            "ji": ji[:4] if ji else [],
            "chong": lunar.getDayChongDesc() or "",
        }
