# 鑫哥日历

鑫哥日历是一款 Windows 桌面日历工具，当前重点接管系统任务栏右下角时间区域：点击系统时间/日期时弹出本应用日历，并阻止 Windows 默认日历面板弹出。

## 当前版本

- 版本：0.1.1
- 平台：Windows 10 / Windows 11
- 安装包：`installer/鑫哥日历_安装_v0.1.1.exe`

## 0.1.1 更新内容

- 接管任务栏右下角系统时间/日期点击行为，点击后弹出鑫哥日历。
- 再次点击系统时间/日期区域时关闭日历。
- 日历固定显示在右下角，不支持拖动，失焦后不自动关闭。
- 右键系统时间/日期区域显示菜单，包含“任务栏时钟设置”和“退出”。
- 移除托盘图标入口，不再占用折叠任务栏图标区域。
- 修复低级鼠标钩子在 64 位 Windows 下可能安装失败的问题。
- 更新安装包打包配置，确保 QML 界面资源被打入安装包。

## 使用方式

1. 安装 `installer/鑫哥日历_安装_v0.1.1.exe`。
2. 启动鑫哥日历。
3. 点击 Windows 任务栏右下角时间/日期区域打开日历。
4. 再次点击同一区域关闭日历。
5. 右键时间/日期区域可打开菜单或退出应用。

## 开发运行

```powershell
pip install -r requirements.txt
python main.py
```

## 打包

```powershell
python -m PyInstaller --clean -y "鑫哥日历.spec"
python tools\build_installer.py
```

打包依赖：

- Python 3.13
- PySide6
- PyInstaller
- Inno Setup 6

## 项目结构

```text
marvis-calendar/
├── main.py
├── src/
│   ├── app.py
│   ├── services/
│   │   └── clock_hook.py
│   ├── qml/
│   └── window_controller.py
├── tools/
│   └── build_installer.py
├── installer/
└── 鑫哥日历.spec
```
