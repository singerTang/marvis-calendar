# 鑫哥日历（Marvis Calendar）

一款面向 Windows 10/11 的桌面日历工具，聚合公历、农历、节气、黄历宜忌、天气和日程提醒。项目采用 Python + PySide6 + QML 实现，主打轻量、本地运行、无边框悬浮窗口和深色玻璃质感界面。

> 当前版本：`v0.1.0`  
> 平台定位：Windows 桌面端  
> 项目目录：`marvis-calendar/`

---

## 项目定位

鑫哥日历希望解决一个很具体的问题：打开一个轻量桌面窗口，就能同时看到今天、这个月、农历、节气、宜忌、天气和日程信息，而不需要在多个应用之间切换。

核心体验：

- 一屏查看月历、农历、节气、宜忌、天气和日程。
- 支持 Windows 桌面悬浮窗口，界面无边框、可拖动。
- 本地 SQLite 存储日程数据，天气模块可联网获取。
- 使用 QML 构建界面，便于快速调整视觉和交互。

---

## 功能特性

| 功能 | 说明 |
|---|---|
| 月历视图 | 展示当前月份日期、周末、节日、节气、农历日期 |
| 日期选中 | 当前日期蓝色填充，点击日期蓝色描边，悬停灰色底色 |
| 农历信息 | 显示农历月日、干支年份、节气等信息 |
| 黄历宜忌 | 展示当日宜做事项、忌做事项、下一节气 |
| 天气信息 | 自动定位城市并获取当前天气，支持中英文天气描述映射 |
| 日程区域 | 展示当日事件，提供添加日程入口 |
| 系统托盘 | 支持托盘驻留，便于后台提醒 |
| 安装包 | 支持 PyInstaller + Inno Setup 打包为 Windows 安装程序 |

---

## 界面结构

当前主界面采用左右双卡片布局：

```text
┌──────────────────────────────────────────────┐
│ 鑫哥日历窗口                                  │
├───────────────┬──────────────────────────────┤
│ 左侧信息卡     │ 右侧月历卡                    │
│               │                              │
│ 大号当前时间   │ 2026年6月              ‹ ›    │
│ 日期 + 星期    │ 一 二 三 四 五 六 日           │
│ 农历摘要       │ 1  2  3  4  5  6  7           │
│ 天气 + 温度    │ 8  9 10 11 12 13 14           │
│ 宜忌标签       │ ...                          │
│ 下一节气       │                              │
│ 日程列表       │                              │
└───────────────┴──────────────────────────────┘
```

---

## 技术栈

| 类型 | 技术 |
|---|---|
| 语言 | Python 3 |
| UI 框架 | PySide6 / Qt Quick / QML |
| 数据库 | SQLite |
| 农历计算 | lunar-python |
| 网络请求 | httpx |
| 打包 | PyInstaller、Inno Setup |
| 测试 | unittest、QML 静态检查 |

---

## 项目结构

```text
marvis-calendar/
├── main.py                         # 应用启动入口
├── requirements.txt                # Python 依赖
├── 鑫哥日历.iss                    # Inno Setup 安装脚本
├── MarvisCalendar_PRD.md           # 产品需求与设计记录
├── src/
│   ├── app.py                      # 主应用初始化、QML 加载、窗口设置
│   ├── bridge.py                   # Python 与 QML 的桥接层
│   ├── shell.py                    # 系统托盘与桌面外壳能力
│   ├── assets/
│   │   └── app.ico                 # 应用图标
│   ├── models/
│   │   ├── database.py             # SQLite 初始化和数据访问
│   │   └── sync.py                 # 同步模型预留
│   ├── services/
│   │   ├── calendar.py             # 公历、农历、节日、节气服务
│   │   ├── almanac.py              # 黄历宜忌服务
│   │   ├── weather.py              # 天气服务、缓存、中英文映射
│   │   └── reminder.py             # 日程提醒服务
│   └── qml/
│       ├── main.qml                # 主窗口布局
│       ├── CalendarGrid.qml        # 月历网格
│       ├── DetailPane.qml          # 左侧日期详情与日程
│       ├── SettingsPanel.qml       # 设置面板
│       ├── TodoList.qml            # 待办列表
│       └── MarvisTabBar.qml        # 导航栏组件
├── tests/
│   ├── test_calendar_grid_layout.py # QML 布局与交互回归测试
│   └── test_weather.py              # 天气中文映射回归测试
└── tools/
    ├── make_icon.py                # 图标生成工具
    └── build_installer.py          # 调用 Inno Setup 构建安装包
```

---

## 快速开始

### 1. 克隆项目

```bash
git clone git@github.com:singerTang/marvis-calendar.git
cd marvis-calendar
```

如果你是在当前仓库结构下运行，实际项目目录在：

```bash
cd marvis-calendar
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动应用

```bash
python main.py
```

---

## 测试

在仓库根目录执行：

```bash
python -m unittest discover -s marvis-calendar\tests
```

编译检查：

```bash
python -m compileall -q marvis-calendar\src marvis-calendar\tests
```

QML 静态检查：

```bash
pyside6-qmllint marvis-calendar\src\qml\main.qml marvis-calendar\src\qml\DetailPane.qml marvis-calendar\src\qml\CalendarGrid.qml
```

---

## 打包说明

项目当前支持打包为 Windows 安装程序。

### 1. 生成图标

```bash
python tools/make_icon.py
```

### 2. 构建安装包

需要先安装 Inno Setup 6。

```bash
python tools/build_installer.py
```

构建完成后，安装包默认输出到：

```text
marvis-calendar\installer\鑫哥日历_安装_v0.1.0.exe
```

当前安装包大小约为：

```text
91.26 MB
```

---

## 天气模块说明

天气服务位于：

```text
marvis-calendar/src/services/weather.py
```

主要能力：

- 使用 `wttr.in` 免费天气接口。
- 通过 IP 自动定位城市。
- 30 分钟本地缓存，减少重复请求。
- 网络失败时返回缓存或降级数据。
- 对常见英文天气描述做中文映射，例如：
  - `Sunny` → `晴`
  - `Partly cloudy` → `多云`
  - `Light drizzle` → `小雨`
  - `Smoky haze` → `霾`
  - `Thunderstorm` → `雷阵雨`

---

## 数据存储

应用使用 SQLite 存储本地数据，数据库位置：

```text
%APPDATA%\MarvisCalendar\marvis.db
```

主要数据：

- 日程事件
- 待办事项
- 设置项

---

## 发布方式

推荐通过 GitHub Releases 发布安装包，而不是直接把 `.exe` 提交到 Git 仓库。

Release 建议信息：

| 字段 | 内容 |
|---|---|
| Tag | `v0.1.0` |
| Title | `鑫哥日历 v0.1.0` |
| Asset | `鑫哥日历_安装_v0.1.0.exe` |

---

## 当前状态

- 已完成基础月历视图。
- 已接入农历、节气、黄历宜忌。
- 已接入天气服务和中文映射。
- 已实现左侧今日信息卡与右侧月历卡布局。
- 已实现基础日程展示区域。
- 已支持 Windows 安装包构建。

---

## 后续计划

- 完善日程新增、编辑、删除流程。
- 完善待办列表和底部导航切换。
- 增加设置项持久化。
- 优化天气城市配置和刷新体验。
- 增加更多 UI 自动化或截图回归测试。
- 发布正式 GitHub Release 下载页。

---

## 许可证

当前项目尚未声明开源许可证。如计划公开发布，建议补充 `LICENSE` 文件。
