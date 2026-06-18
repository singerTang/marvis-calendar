import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    clip: true

    // 颜色由父级传入（main.qml 的 id: tabBar 下方设置了这些属性，但 DetailPane 不同
    // 我们直接从 Window 读取）
    property color accent: "#5e8cf0"
    property color textPrimary: Qt.rgba(1, 1, 1, 0.95)
    property color textSecondary: Qt.rgba(1, 1, 1, 0.75)
    property color textTertiary: Qt.rgba(1, 1, 1, 0.52)

    property date selectedDate: new Date()
    property var weatherData: ({})
    property string currentTime: "00:00:00"
    property string dateStr: ""
    property var lunarData: ({})
    property var almanacData: ({})
    property var events: ([])
    property var nextTerm: ({})

    function refresh(ds) {
        dateStr = ds
        var detail = bridge.day_detail(ds)
        lunarData = detail.lunar
        almanacData = detail.almanac
        events = detail.events
        nextTerm = detail.nextTerm
    }

    function pad(n) {
        return n < 10 ? "0" + n : "" + n
    }

    function updateClock() {
        var now = new Date()
        currentTime = pad(now.getHours()) + ":" + pad(now.getMinutes()) + ":" + pad(now.getSeconds())
    }

    function weekdayText(d) {
        return ["星期日","星期一","星期二","星期三","星期四","星期五","星期六"][d.getDay()]
    }

    function selectedDateText() {
        var d = root.selectedDate
        return d.getFullYear() + "年" + (d.getMonth() + 1) + "月" + d.getDate() + "日 " + weekdayText(d)
    }

    function lunarSummary() {
        if (!lunarData || !lunarData.year_cn) return ""
        return lunarData.month_cn + "月" + lunarData.day_cn + " · " + lunarData.ganzhi_year + "年"
    }

    Component.onCompleted: updateClock()

    // 日程变更后，若变更日期为当前所选日期则刷新列表
    // 用 Connections 由引擎管理生命周期，避免组件重建时重复连接
    Connections {
        target: bridge
        function onEventsChanged(d) {
            if (d === root.dateStr) root.refresh(root.dateStr)
        }
    }

    // 日程新增/编辑/删除对话框
    EventDialog {
        id: eventDialog
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: root.updateClock()
    }

    ColumnLayout {
        anchors { fill: parent; margins: 10 }
        spacing: 10

        // ─── 今日信息头部：时间、日期、农历、天气 ───────────────────────
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 92
            spacing: 10

            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: 4

                Text {
                    id: currentTimeText
                    text: root.currentTime
                    color: root.textPrimary
                    font.pixelSize: 36
                    font.weight: 800
                    font.letterSpacing: 1
                }

                Text {
                    text: root.selectedDateText()
                    color: root.textSecondary
                    font.pixelSize: 12
                }

                Text {
                    text: root.lunarSummary()
                    color: root.textTertiary
                    font.pixelSize: 11
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }

            ColumnLayout {
                id: weatherHeader
                Layout.minimumWidth: 68
                width: 68
                Layout.alignment: Qt.AlignTop
                spacing: 2

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.weatherData.icon || "⛅"
                    font.pixelSize: 30
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.weatherData.loading ? "..." : ((root.weatherData.temp || "--") + "℃")
                    color: root.textPrimary
                    font.pixelSize: 14
                    font.weight: 700
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.weatherData.loading ? "" : (root.weatherData.text || "")
                    color: root.textTertiary
                    font.pixelSize: 10
                    elide: Text.ElideRight
                    width: 68
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        ColumnLayout {
            spacing: 6
            Layout.fillWidth: true

            // 宜忌标签
            Flow {
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: almanacData && almanacData.yi ? almanacData.yi.slice(0, 3) : []
                    Rectangle {
                        width: tagText.width + 14; height: 20; radius: 7
                        color: Qt.rgba(0.47, 0.86, 0.47, 0.08)
                        border { width: 1; color: Qt.rgba(0.47, 0.86, 0.47, 0.15) }
                        Text {
                            id: tagText
                            anchors.centerIn: parent
                            text: "宜 " + modelData
                            color: Qt.rgba(0.47, 0.86, 0.47, 0.82)
                            font.pixelSize: 10; font.weight: 500
                        }
                    }
                }
                Repeater {
                    model: almanacData && almanacData.ji ? almanacData.ji.slice(0, 2) : []
                    Rectangle {
                        width: badText.width + 14; height: 20; radius: 7
                        color: Qt.rgba(1, 0.51, 0.43, 0.08)
                        border { width: 1; color: Qt.rgba(1, 0.51, 0.43, 0.15) }
                        Text {
                            id: badText
                            anchors.centerIn: parent
                            text: "忌 " + modelData
                            color: Qt.rgba(1, 0.51, 0.43, 0.82)
                            font.pixelSize: 10; font.weight: 500
                        }
                    }
                }
            }
        }

        // 下一节气
        Rectangle {
            Layout.fillWidth: true; height: 24; radius: 8
            visible: root.nextTerm && root.nextTerm.name ? true : false
            color: Qt.rgba(0.96, 0.65, 0.14, 0.08)
            border { width: 1; color: Qt.rgba(0.96, 0.65, 0.14, 0.15) }
            Text {
                anchors.centerIn: parent
                text: root.nextTerm && root.nextTerm.name
                      ? ("下一节气 · " + root.nextTerm.name + " " + root.nextTerm.date) : ""
                color: Qt.rgba(0.96, 0.65, 0.14, 0.85)
                font.pixelSize: 11; font.weight: 500
            }
        }

        // ─── 日程 ─────────────────────────────────────────────────────
        Text {
            text: "日程"
            color: root.textTertiary
            font.pixelSize: 10; font.weight: 600; font.letterSpacing: 1
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: events
            spacing: 5
            clip: true
            delegate: Rectangle {
                width: ListView.view.width; height: 44; radius: 9
                color: Qt.rgba(1,1,1,0.03)
                border { width: 1; color: Qt.rgba(1,1,1,0.06) }

                RowLayout {
                    anchors { fill: parent; margins: 10 }
                    Rectangle {
                        width: 3; height: parent.height * 0.6; radius: 2
                        color: modelData.color || root.accent
                        Layout.alignment: Qt.AlignVCenter
                    }
                    ColumnLayout { spacing: 2
                        Text {
                            text: modelData.time; font.pixelSize: 10
                            color: root.accent; font.weight: 500
                        }
                        Text {
                            text: modelData.title; font.pixelSize: 12
                            color: root.textPrimary
                        }
                    }
                }

                // 点击列表项进入编辑（取完整事件回填表单；事件不存在则不打开）
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        var ev = bridge.event_for_edit(modelData.id)
                        if (ev) eventDialog.openEdit(ev)
                    }
                }
            }

            // 空状态
            Rectangle {
                anchors.fill: parent
                color: "transparent"
                visible: events.length === 0
                Text {
                    anchors.centerIn: parent
                    text: "暂无日程"
                    color: root.textTertiary
                    font.pixelSize: 11
                }
            }
        }

        // 添加按钮
        Rectangle {
            Layout.fillWidth: true; height: 34; radius: 9
            color: Qt.rgba(0.37, 0.55, 0.94, 0.06)
            border { width: 1; color: Qt.rgba(0.37, 0.55, 0.94, 0.18) }
            Text {
                anchors.centerIn: parent
                text: "+ 添加日程"
                color: Qt.rgba(0.37, 0.55, 0.94, 0.72)
                font.pixelSize: 11; font.weight: 500
            }
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: eventDialog.openCreate(root.dateStr)
            }
        }
    }
}
