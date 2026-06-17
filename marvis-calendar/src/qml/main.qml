import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: root
    width: 680
    height: 780
    visible: true
    flags: Qt.FramelessWindowHint | Qt.Window
    color: "transparent"

    // ─── 状态 ─────────────────────────────────────────────────────────
    property date selectedDate: new Date()
    property var weatherData: ({})
    property bool isLoading: true

    // ─── 颜色 ─────────────────────────────────────────────────────────
    readonly property color accent: "#5e8cf0"
    readonly property color glassBg: Qt.rgba(0.06, 0.06, 0.08, 0.92)
    readonly property color cardBg: Qt.rgba(0.08, 0.08, 0.1, 0.95)
    readonly property color cardBorder: Qt.rgba(1, 1, 1, 0.08)
    readonly property color textPrimary: Qt.rgba(1, 1, 1, 0.95)
    readonly property color textSecondary: Qt.rgba(1, 1, 1, 0.75)
    readonly property color textTertiary: Qt.rgba(1, 1, 1, 0.52)

    // ─── 主容器 ─────────────────────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        radius: 16
        color: root.glassBg
        antialiasing: true
        border.width: 0

        // ─── 加载动画 ───────────────────────────────────────────────────
        Item {
            id: loadingOverlay
            anchors.fill: parent
            visible: root.isLoading
            z: 100

            Rectangle {
                anchors.fill: parent
                radius: 16
                color: Qt.rgba(0.06, 0.06, 0.08, 0.98)

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 16

                    Row {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 6
                        Repeater {
                            model: 3
                            Rectangle {
                                width: 8; height: 8; radius: 4
                                color: root.accent
                                SequentialAnimation on opacity {
                                    loops: Animation.Infinite
                                    running: root.isLoading
                                    PauseAnimation { duration: index * 150 }
                                    NumberAnimation { from: 0.3; to: 1.0; duration: 300 }
                                    NumberAnimation { from: 1.0; to: 0.3; duration: 300 }
                                }
                            }
                        }
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "正在加载..."
                        color: root.textSecondary
                        font.pixelSize: 12
                    }
                }
            }
        }

        // ─── 标题栏 ───────────────────────────────────────────────────
        Item {
            id: titleBar
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: 12
            z: 10

            // 拖拽移动
            MouseArea {
                anchors.fill: parent
                property point lastPos: Qt.point(0, 0)
                onPressed: { lastPos = Qt.point(mouse.x, mouse.y) }
                onPositionChanged: {
                    root.x += mouse.x - lastPos.x
                    root.y += mouse.y - lastPos.y
                }
            }
        }

        // ─── 双卡片区域 ───────────────────────────────────────────────
        RowLayout {
            anchors { top: parent.top; left: parent.left; right: parent.right; bottom: parent.bottom }
            anchors { leftMargin: 12; rightMargin: 12; topMargin: 12; bottomMargin: 12 }
            spacing: 12

            // 左侧卡片：日程详情
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 0.85
                radius: 12
                color: root.cardBg
                border { width: 1; color: root.cardBorder }

                DetailPane {
                    id: detailPane
                    anchors.fill: parent
                    anchors.margins: 8
                    selectedDate: root.selectedDate
                    weatherData: root.weatherData
                }
            }

            // 右侧卡片：日历
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 1.35
                radius: 12
                color: root.cardBg
                border { width: 1; color: root.cardBorder }

                CalendarGrid {
                    id: calendarGrid
                    anchors.fill: parent
                    anchors.margins: 4
                    selectedDate: root.dateKey(root.selectedDate)
                    onDayClicked: function(dateStr) {
                        root.selectedDate = new Date(dateStr)
                        detailPane.refresh(dateStr)
                    }
                }
            }
        }
    }

    // ─── 初始化 ─────────────────────────────────────────────────────────
    Component.onCompleted: {
        bridge.weatherReady.connect(function(weather) {
            root.weatherData = weather
            root.isLoading = false
        })
    }

    Timer {
        interval: 100; running: true; repeat: false
        onTriggered: {
            var d = root.selectedDate
            detailPane.refresh(root.dateKey(d))
            bridge.fetch_weather_async()
        }
    }

    Timer {
        interval: 2000; running: true; repeat: false
        onTriggered: {
            if (root.isLoading) root.isLoading = false
        }
    }

    function pad(n) { return n < 10 ? "0" + n : "" + n }
    function dateKey(d) {
        return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate())
    }
}
