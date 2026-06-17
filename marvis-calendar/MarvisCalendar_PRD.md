# Marvis Calendar — PRD 与开发思路

## 一、产品概述

**Marvis Calendar** 是一款 Windows 11 桌面日历工具，融合中国传统农历、黄历宜忌、天气预报与日程管理。视觉风格对标 iOS 毛玻璃（Acrylic），无边框悬浮窗口，可拖拽、置顶。

### 核心价值
- 一屏查看公历/农历/节气/宜忌/天气/日程
- Windows 原生 DWM 毛玻璃，融入桌面环境
- 轻量本地运行，SQLite 存储，无需网络（天气可选）

---

## 二、技术架构

```
Platform: Windows 10/11 (Win32)
Runtime:  Python 3.11+
UI:       PySide6 (Qt 6.5+) QML
DB:       SQLite 3 (WAL 模式)
日历:     lunar-python (1900-2100)
节气:     寿星历算法
毛玻璃:   DWM API (SystemBackdropType / SetWindowCompositionAttribute)
```

### 模块分层

| 层 | 模块 | 职责 |
|---|---|---|
| 入口 | `main.py` | 启动入口、虚拟环境配置 |
| 窗口 | `src/app.py` | DWM 毛玻璃初始化、窗口无边框、QML 加载 |
| 数据 | `src/models/database.py` | SQLite 建表、CRUD、migration |
| 服务 | `src/services/calendar.py` | 公历/农历转换、节气计算、节假日 |
| 服务 | `src/services/almanac.py` | 宜忌、冲煞、黄历 |
| 服务 | `src/services/weather.py` | 天气 API 调用 + 缓存 |
| 服务 | `src/services/reminder.py` | 日程提醒 |
| 服务 | `src/services/sync.py` | 数据同步 |
| 界面 | `src/qml/main.qml` | 主窗口容器、颜色系统、布局 |
| 界面 | `src/qml/CalendarGrid.qml` | 月历网格 |
| 界面 | `src/qml/DetailPane.qml` | 日期详情、宜忌、日程列表 |
| 界面 | `src/qml/MarvisTabBar.qml` | 底部导航栏 |
| 界面 | `src/qml/WeekView.qml` | 周视图 |
| 界面 | `src/qml/TodoList.qml` | 待办列表 |

---

## 三、数据库设计

```sql
-- schema 版本
PRAGMA user_version = 1;

-- 事件表
CREATE TABLE events (
    id          TEXT PRIMARY KEY,           -- UUID7
    title       TEXT NOT NULL,
    start_time  TEXT NOT NULL,              -- ISO 8601
    end_time    TEXT,
    all_day     INTEGER DEFAULT 0,
    category    TEXT DEFAULT '',
    color       TEXT DEFAULT '#5e8cf0',
    notes       TEXT DEFAULT '',
    repeat_rule TEXT DEFAULT '',            -- iCalendar RRULE
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- 待办表
CREATE TABLE todos (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    due_date    TEXT,
    priority    INTEGER DEFAULT 0,          -- 0=无 1=低 2=中 3=高
    completed   INTEGER DEFAULT 0,
    list_name   TEXT DEFAULT '默认',
    notes       TEXT DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- 设置表
CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### 数据库原则
- 主键全部 UUID7（时间有序）
- thread-local 连接，避免跨线程冲突
- WAL 模式提升并发读性能

---

## 四、毛玻璃实现路径（降级链）

```
1. Win11 22H2+  → DwmSetWindowAttribute(DWMWA_SYSTEMBACKDROP_TYPE, TABBEDWINDOW)
2. Win10 1803+  → SetWindowCompositionAttribute(ACCENT_ENABLE_ACRYLICBLURBEHIND)
3. Win10 早期   → DwmEnableBlurBehindWindow
4. 全部失败     → 纯半透明黑色背景（不模糊但保留透明感）
```

配合措施：
- `SetWindowLongW(GWL_STYLE, WS_POPUP | WS_THICKFRAME | ...)` 去掉系统标题栏
- `DwmExtendFrameIntoClientArea(-1, -1, -1, -1)` 将 DWM 边框延伸到整个客户区
- QML Window `color: "transparent"` 背景透明，让 DWM 模糊穿透
- QML 主 Rectangle `color: rgba(6,6,8,0.65)` 半透明叠加，透出模糊后的桌面

---

## 五、ui开发

### 5.1 颜色系统（暗色基础）

| Token | 值 | 用途 |
|---|---|---|
| accent | #5e8cf0 | 主题色（蓝紫） |
| glassBg | rgba(6,6,8,0.65) | 毛玻璃底色 |
| glassBorder | rgba(255,255,255,0.08) | 玻璃边框 |
| textPrimary | rgba(255,255,255,0.95) | 主文字 |
| textSecondary | rgba(255,255,255,0.75) | 次要文字 |
| textTertiary | rgba(255,255,255,0.52) | 辅助文字 |
| weekendColor | rgba(255,140,120,0.68) | 周末/节假日 |

### 5.2 布局结构

```
┌────────────────────────────────┐
│  ◀ 2026年6月 ▶     ☀ 28° 北京 │  ← 拖拽标题栏
├───────────────┬────────────────┤
│  6月16日 周三  │  一 二 三 … 日 │
│  农历五月廿一  │  1  2  3  4 … │
│  宜 嫁娶 出行  │  7  8  9 10 … │
│  忌 动土       │ 14 15 16 17 … │
│  🐉 端午节4天后 │ 21 22 23 24 … │
│               │ 28 29 30      │
│  日程          │               │
│  ● 团队周会    │               │
│  ● 产品评审    │               │
│  + 添加日程    │               │
├───────────────┴────────────────┤
│   ☾ 月历  ◷ 周历  ☀ 日历  ☑ 待办  │
└────────────────────────────────┘
```

### 5.3 交互细节
- 窗口可拖拽（标题栏 MouseArea）
- 月份左右箭头切换
- 日期格子点击 → 左侧详情面板刷新
- 底部 Tab 切换视图
- 日程列表项左滑删除（待实现）
- 添加按钮弹出模态表单（待实现）

---

## 六、核心算法

### 6.1 农历计算
- 库：`lunar-python`，覆盖 1900-2100
- API：`Solar.fromYmd(y,m,d).getLunar()` 获取农历
- 节气：寿星历算法，`Solar.fromYmd(y,m,d).getJieQi()` 返回最近节气
- 节假日：`Solar.getFestivals()` + `Lunar.getFestivals()`

### 6.2 黄历（宜忌）
- `AlmanacService.daily_almanac_compact(date)` 返回当日宜忌列表
- 数据源：内置黄历规则表，基于农历日/月干支组合
- 冲煞：`Lunar.getDayZhi()` → 查询冲煞规则

### 6.3 天气
- 优先：和风天气 API → 缓存 30 分钟
- 回退：Open-Meteo 免费 API
- 自动检测 IP 定位城市

---

## 七、项目文件清单

```
marvis-calendar/
├── main.py                      # 入口
├── requirements.txt             # 依赖
├── src/
│   ├── app.py                   # 窗口 & DWM 毛玻璃
│   ├── models/
│   │   └── database.py          # SQLite 数据库
│   ├── services/
│   │   ├── calendar.py          # 日历服务
│   │   ├── almanac.py           # 黄历服务
│   │   ├── weather.py           # 天气服务
│   │   ├── reminder.py          # 提醒服务
│   │   └── sync.py              # 同步服务
│   └── qml/
│       ├── main.qml             # 主窗口 + 颜色系统
│       ├── CalendarGrid.qml     # 月历网格
│       ├── DetailPane.qml       # 详情面板
│       ├── MarvisTabBar.qml     # 底部导航
│       ├── WeekView.qml         # 周视图
│       └── TodoList.qml         # 待办列表
└── tests/
```

---

## 八、关键决策记录

| # | 决策 | 理由 |
|---|---|---|
| 1 | PySide6 而非 PyQt6 | LGPL 许可，商业友好 |
| 2 | QML 声明式 UI 而非 QtWidgets | 毛玻璃/动画/响应式更适合 QML |
| 3 | DWM API 而非 Qt 内置模糊 | Qt 内置 `FastBlur` 只模糊自身内容，DWM 可透出桌面背景 |
| 4 | lunar-python 而非自写农历 | 维护成本低，覆盖 1900-2100 |
| 5 | UUID7 主键 | 时间有序，便于按创建时间检索 |
| 6 | WAL 模式 | 读写并发不阻塞 |
| 7 | 三级毛玻璃降级链 | 适配 Win10/Win11 各种版本 |
| 8 | 窗口无边框由 Python 侧 SetWindowLongW 实现 | QML flags 在窗口已创建后不宜修改，Python 侧更可控 |
| 9 | TabBar 图标用 Unicode 而非 Canvas SVG Path2D | Qt6 QML Canvas 对 Path2D 支持不稳定，Unicode 可靠且跨平台 |
| 10 | 颜色 Token 在子组件中自行声明 | 避免 `parent.parent.parent.xxx` 脆弱引用链 |
| 11 | 日程数据当前为 stub | 数据库 CRUD 已就位，UI 先走通再接入真实数据 |
