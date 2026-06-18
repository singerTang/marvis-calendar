"""日程（events）CRUD 单元测试。

覆盖三类场景：
- 纯逻辑：Bridge 静态方法 _build_times / _parse_event
- 集成：真实 SQLite 临时库 + Database + Bridge 的增删改查往返
- 信号：eventsChanged 的发射与参数

作者：singerTang <109527086+singerTang@users.noreply.github.com>
"""

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

# 将 src 目录加入 sys.path，使 bridge / models.database 可按其内部相对结构导入
_SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from models.database import Database  # noqa: E402

_bridge_module = importlib.import_module("bridge")
Bridge = _bridge_module.Bridge

# QSignalSpy / QCoreApplication 用于信号断言；不可用时降级跳过信号用例
try:
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtTest import QSignalSpy

    _SIGNAL_SUPPORT = True
except ImportError:  # pragma: no cover - 取决于运行环境
    _SIGNAL_SUPPORT = False


# 单进程内 QCoreApplication 只能存在一个实例，复用全局引用
_QAPP = None
if _SIGNAL_SUPPORT:
    _QAPP = QCoreApplication.instance() or QCoreApplication(sys.argv[:1])


def _make_event_data(**overrides):
    """构造一份默认合法的日程表单数据，便于按需覆盖字段。"""
    data = {
        "title": "测试日程",
        "date": "2026-06-18",
        "all_day": False,
        "start_hhmm": "09:00",
        "end_hhmm": "10:00",
        "reminder_minutes": -1,
        "color": "#5e8cf0",
        "notes": "",
    }
    data.update(overrides)
    return data


class BuildTimesTest(unittest.TestCase):
    """_build_times 纯逻辑校验。"""

    def test_all_day_returns_midnight_start_and_none_end(self):
        start, end, error = Bridge._build_times({"date": "2026-06-18", "all_day": True})
        self.assertEqual(start, "2026-06-18T00:00:00", "全天事件开始应为当日零点")
        self.assertIsNone(end, "全天事件结束时间应为 None")
        self.assertEqual(error, "", "全天事件不应报错")

    def test_normal_period_builds_iso_range(self):
        start, end, error = Bridge._build_times(
            {"date": "2026-06-18", "all_day": False, "start_hhmm": "09:00", "end_hhmm": "10:30"}
        )
        self.assertEqual(start, "2026-06-18T09:00:00", "开始时间 ISO 拼装错误")
        self.assertEqual(end, "2026-06-18T10:30:00", "结束时间 ISO 拼装错误")
        self.assertEqual(error, "", "正常时段不应报错")

    def test_missing_date_reports_error(self):
        start, end, error = Bridge._build_times({"all_day": True})
        self.assertIsNone(start)
        self.assertIsNone(end)
        self.assertEqual(error, "缺少日期", "缺少日期应返回对应错误")

    def test_invalid_start_format_reports_error(self):
        start, end, error = Bridge._build_times(
            {"date": "2026-06-18", "all_day": False, "start_hhmm": "9:00", "end_hhmm": "10:00"}
        )
        self.assertIsNone(start)
        self.assertEqual(error, "开始时间格式不正确", "非法开始时间应被拦截")

    def test_invalid_end_format_reports_error(self):
        start, end, error = Bridge._build_times(
            {"date": "2026-06-18", "all_day": False, "start_hhmm": "09:00", "end_hhmm": "25:00"}
        )
        self.assertIsNone(start)
        self.assertEqual(error, "结束时间格式不正确", "非法结束时间应被拦截")

    def test_end_before_start_reports_error(self):
        start, end, error = Bridge._build_times(
            {"date": "2026-06-18", "all_day": False, "start_hhmm": "10:00", "end_hhmm": "09:00"}
        )
        self.assertIsNone(start)
        self.assertEqual(error, "结束时间不能早于开始时间", "结束早于开始应报错")

    def test_end_equals_start_is_allowed(self):
        # 现有实现使用 end < start 判定，故 end == start 应被放行
        start, end, error = Bridge._build_times(
            {"date": "2026-06-18", "all_day": False, "start_hhmm": "09:00", "end_hhmm": "09:00"}
        )
        self.assertEqual(error, "", "结束等于开始按现有实现应被允许")
        self.assertEqual(start, "2026-06-18T09:00:00")
        self.assertEqual(end, "2026-06-18T09:00:00")


class ParseEventTest(unittest.TestCase):
    """_parse_event 纯逻辑校验。"""

    def test_empty_title_reports_error(self):
        params, error = Bridge._parse_event(_make_event_data(title="   "))
        self.assertIsNone(params)
        self.assertEqual(error, "标题不能为空", "空白标题应被拦截")

    def test_title_is_stripped(self):
        params, error = Bridge._parse_event(_make_event_data(title="  会议  "))
        self.assertEqual(error, "")
        self.assertEqual(params["title"], "会议", "标题首尾空格应被去除")

    def test_reminder_minus_one_becomes_none(self):
        params, _ = Bridge._parse_event(_make_event_data(reminder_minutes=-1))
        self.assertIsNone(params["reminder_minutes"], "reminder=-1 应转换为 None")

    def test_reminder_thirty_kept(self):
        params, _ = Bridge._parse_event(_make_event_data(reminder_minutes=30))
        self.assertEqual(params["reminder_minutes"], 30, "reminder=30 应保留为 30")

    def test_empty_color_falls_back_to_default(self):
        params, _ = Bridge._parse_event(_make_event_data(color=""))
        self.assertEqual(params["color"], "#5e8cf0", "空颜色应回退到默认蓝")

    def test_empty_notes_becomes_none(self):
        params, _ = Bridge._parse_event(_make_event_data(notes=""))
        self.assertIsNone(params["notes"], "空备注应转换为 None")


class _BridgeIntegrationBase(unittest.TestCase):
    """集成测试基类：每个用例独立的临时 SQLite 库与 Bridge。"""

    def setUp(self):
        # 使用临时目录承载真实 sqlite 文件，测试结束统一清理，绝不触碰 %APPDATA%
        self._tmp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp_dir.name) / "test.db"
        self.db = Database(db_path)
        self.db.initialize()
        # calendar / almanac / weather 在本组用例中不被触达，传 None 即可
        self.bridge = Bridge(self.db, None, None, None)

    def tearDown(self):
        # 关闭线程局部连接，避免 Windows 下文件占用导致临时目录清理失败
        conn = getattr(self.db._local, "conn", None)
        if conn is not None:
            conn.close()
            self.db._local.conn = None
        self._tmp_dir.cleanup()


class AddEventTest(_BridgeIntegrationBase):
    def test_add_event_success_is_queryable(self):
        result = self.bridge.add_event(_make_event_data(title="晨会", date="2026-06-18"))
        self.assertTrue(result["ok"], "合法日程新增应成功")
        self.assertEqual(result["error"], "")
        self.assertIsNotNone(result["event"])

        rows = self.db.get_events_by_date("2026-06-18")
        self.assertEqual(len(rows), 1, "新增后应能按日期查到 1 条")
        self.assertEqual(rows[0]["title"], "晨会")

    def test_add_event_invalid_title_does_not_write(self):
        result = self.bridge.add_event(_make_event_data(title="", date="2026-06-18"))
        self.assertFalse(result["ok"], "空标题应新增失败")
        self.assertEqual(result["error"], "标题不能为空")
        self.assertIsNone(result["event"])

        rows = self.db.get_events_by_date("2026-06-18")
        self.assertEqual(len(rows), 0, "校验失败不应写库")


class UpdateEventTest(_BridgeIntegrationBase):
    def test_update_changes_title_and_time(self):
        added = self.bridge.add_event(
            _make_event_data(title="旧标题", date="2026-06-18", start_hhmm="09:00", end_hhmm="10:00")
        )
        eid = added["event"]["id"]

        result = self.bridge.update_event(
            eid,
            _make_event_data(title="新标题", date="2026-06-18", start_hhmm="14:00", end_hhmm="15:00"),
        )
        self.assertTrue(result["ok"], "合法更新应成功")

        edit = self.bridge.event_for_edit(eid)
        self.assertEqual(edit["title"], "新标题", "更新后标题应变化")
        self.assertEqual(edit["start_hhmm"], "14:00", "更新后开始时间应变化")
        self.assertEqual(edit["end_hhmm"], "15:00", "更新后结束时间应变化")


class DeleteEventTest(_BridgeIntegrationBase):
    def test_delete_removes_event(self):
        added = self.bridge.add_event(_make_event_data(date="2026-06-18"))
        eid = added["event"]["id"]

        ok = self.bridge.delete_event(eid)
        self.assertTrue(ok, "删除应返回 True")
        self.assertEqual(len(self.db.get_events_by_date("2026-06-18")), 0, "删除后应查不到")

    def test_delete_nonexistent_is_idempotent(self):
        ok = self.bridge.delete_event("not-a-real-id")
        self.assertTrue(ok, "删除不存在 id 应幂等返回 True")


class EventForEditTest(_BridgeIntegrationBase):
    def test_all_day_event_has_empty_start_hhmm(self):
        added = self.bridge.add_event(_make_event_data(title="全天", date="2026-06-18", all_day=True))
        eid = added["event"]["id"]
        edit = self.bridge.event_for_edit(eid)
        self.assertTrue(edit["all_day"], "应识别为全天")
        self.assertEqual(edit["start_hhmm"], "", "全天事件开始时分应为空")
        self.assertEqual(edit["end_hhmm"], "", "全天事件结束时分应为空")

    def test_timed_event_has_correct_hhmm(self):
        added = self.bridge.add_event(
            _make_event_data(date="2026-06-18", start_hhmm="08:30", end_hhmm="09:45")
        )
        eid = added["event"]["id"]
        edit = self.bridge.event_for_edit(eid)
        self.assertFalse(edit["all_day"])
        self.assertEqual(edit["start_hhmm"], "08:30", "非全天开始时分回填错误")
        self.assertEqual(edit["end_hhmm"], "09:45", "非全天结束时分回填错误")

    def test_nonexistent_id_returns_none(self):
        self.assertIsNone(self.bridge.event_for_edit("not-a-real-id"), "不存在 id 应返回 None")


class ReminderRoundTripTest(_BridgeIntegrationBase):
    def test_reminder_thirty_round_trip(self):
        added = self.bridge.add_event(_make_event_data(date="2026-06-18", reminder_minutes=30))
        eid = added["event"]["id"]
        edit = self.bridge.event_for_edit(eid)
        self.assertEqual(edit["reminder_minutes"], 30, "存 30 应读回 30")

    def test_reminder_none_round_trip_reads_minus_one(self):
        added = self.bridge.add_event(_make_event_data(date="2026-06-18", reminder_minutes=-1))
        eid = added["event"]["id"]
        edit = self.bridge.event_for_edit(eid)
        self.assertEqual(edit["reminder_minutes"], -1, "存 None 应读回 -1")


@unittest.skipUnless(_SIGNAL_SUPPORT, "QSignalSpy 不可用，跳过信号用例")
class EventsChangedSignalTest(_BridgeIntegrationBase):
    def test_add_success_emits_events_changed_with_date(self):
        spy = QSignalSpy(self.bridge.eventsChanged)
        self.bridge.add_event(_make_event_data(date="2026-06-18"))
        self.assertEqual(spy.count(), 1, "新增成功应触发一次 eventsChanged")
        self.assertEqual(spy.at(0)[0], "2026-06-18", "信号参数应为受影响日期")

    def test_add_failure_does_not_emit(self):
        spy = QSignalSpy(self.bridge.eventsChanged)
        self.bridge.add_event(_make_event_data(title="", date="2026-06-18"))
        self.assertEqual(spy.count(), 0, "校验失败不应触发 eventsChanged")


@unittest.skipUnless(_SIGNAL_SUPPORT, "需要 Qt 环境构造 QJSValue")
class QJSValueArgTest(_BridgeIntegrationBase):
    """回归：复现 QML 传入 QJSValue（而非 dict）的真实场景。

    直接传 dict 的用例会绕过 QML→QJSValue 转换，曾遗漏此路径导致运行时
    AttributeError；此处用 QJSEngine 构造 QJSValue 守护该回归。
    """

    def _make_qjsvalue(self, expr):
        from PySide6.QtQml import QJSEngine
        if not hasattr(self, "_engine"):
            self._engine = QJSEngine()
        return self._engine.evaluate(expr)

    def test_add_event_accepts_qjsvalue(self):
        jsval = self._make_qjsvalue(
            '({title:"龙舟", date:"2026-06-18", all_day:true,'
            ' start_hhmm:"", end_hhmm:"", notes:"明天看龙舟",'
            ' color:"#5e8cf0", reminder_minutes:-1})'
        )
        result = self.bridge.add_event(jsval)
        self.assertTrue(result["ok"], "QJSValue 入参应被接受并新增成功")
        rows = self.db.get_events_by_date("2026-06-18")
        self.assertEqual(len(rows), 1, "QJSValue 新增后应能查到")
        self.assertEqual(rows[0]["title"], "龙舟")

    def test_update_event_accepts_qjsvalue(self):
        added = self.bridge.add_event(_make_event_data(title="旧", date="2026-06-18"))
        eid = added["event"]["id"]
        jsval = self._make_qjsvalue(
            '({title:"新", date:"2026-06-18", all_day:false,'
            ' start_hhmm:"08:00", end_hhmm:"09:00", notes:"",'
            ' color:"#5e8cf0", reminder_minutes:15})'
        )
        result = self.bridge.update_event(eid, jsval)
        self.assertTrue(result["ok"], "QJSValue 入参应被接受并更新成功")
        edit = self.bridge.event_for_edit(eid)
        self.assertEqual(edit["title"], "新", "QJSValue 更新后标题应变化")
        self.assertEqual(edit["reminder_minutes"], 15, "QJSValue 更新后提醒应变化")


if __name__ == "__main__":
    unittest.main()
