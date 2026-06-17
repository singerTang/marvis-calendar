import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    clip: true

    property int currentYear: 2026
    property int currentMonth: 5    // 0-based
    property string selectedDate: ""
    property string hoveredDate: ""  // 悬停的日期
    property var gridData: ([])

    property color accent: "#5e8cf0"
    property color textPrimary: Qt.rgba(1, 1, 1, 0.95)
    property color textSecondary: Qt.rgba(1, 1, 1, 0.75)
    property color textTertiary: Qt.rgba(1, 1, 1, 0.52)
    property color weekendColor: Qt.rgba(1, 0.55, 0.47, 0.68)
    property color festivalColor: "#f5a623"
    property color holidayVacationColor: "#ff6b6b"

    signal dayClicked(string dateStr)

    function loadMonth() {
        gridData = bridge.month_grid(currentYear, currentMonth + 1)
    }

    function prevMonth() {
        if (currentMonth === 0) { currentMonth = 11; currentYear-- }
        else currentMonth--
        loadMonth()
    }

    function nextMonth() {
        if (currentMonth === 11) { currentMonth = 0; currentYear++ }
        else currentMonth++
        loadMonth()
    }

    Component.onCompleted: {
        var t = new Date()
        currentYear = t.getFullYear()
        currentMonth = t.getMonth()
        loadMonth()
    }

    // 鼠标滚轮切换月份
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        onWheel: function(wheel) {
            if (wheel.angleDelta.y > 0) prevMonth()
            else if (wheel.angleDelta.y < 0) nextMonth()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            id: monthHeader
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            Layout.topMargin: 6
            spacing: 8

            Text {
                id: calendarGridMonthLabel
                text: root.currentYear + "年" + (root.currentMonth + 1) + "月"
                color: root.textPrimary
                font.pixelSize: 17
                font.weight: 700
                Layout.alignment: Qt.AlignVCenter
            }

            Item { Layout.fillWidth: true }

            Text {
                text: "‹"
                color: root.textSecondary
                font.pixelSize: 24
                Layout.alignment: Qt.AlignVCenter
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -10
                    onClicked: root.prevMonth()
                }
            }

            Text {
                text: "›"
                color: root.textSecondary
                font.pixelSize: 24
                Layout.alignment: Qt.AlignVCenter
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -10
                    onClicked: root.nextMonth()
                }
            }
        }

        // 星期头
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            spacing: 0
            Repeater {
                model: ["一","二","三","四","五","六","日"]
                Text {
                    Layout.fillWidth: true
                    text: modelData
                    color: index >= 5 ? root.weekendColor : root.textSecondary
                    font.pixelSize: 14; font.weight: 600
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        // 日期网格（6行 x 7列）
        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 7; rows: 6
            rowSpacing: 4; columnSpacing: 0

            Repeater {
                model: root.gridData

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 1

                    // 一个月一页：非本月格子留空白，背景始终透明
                    color: "transparent"

                    property bool isSelected: modelData.date === root.selectedDate
                    property bool isHovered: modelData.date === root.hoveredDate

                    // 日期内容（非本月格子留空白）
                    Item {
                        anchors.fill: parent
                        anchors.margins: 2
                        visible: modelData.isCurrentMonth

                        Item {
                            id: selectedDateContent
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: dayText.top
                            width: Math.max(dayText.paintedWidth, lunarText.paintedWidth)
                            height: dayText.height + lunarText.anchors.topMargin + lunarText.height
                            visible: false
                        }

                        // 今天填充、点击描边、悬停灰底，均包住日期数字和农历文字。
                        Rectangle {
                            id: selectCircle
                            anchors.centerIn: selectedDateContent
                            width: Math.max(44, selectedDateContent.width + 16, selectedDateContent.height + 10)
                            height: width
                            radius: width / 2
                            antialiasing: true
                            z: -1

                            color: {
                                if (modelData.isToday) return root.accent
                                if (isSelected) return "transparent"
                                if (isHovered) return Qt.rgba(1, 1, 1, 0.14)
                                return "transparent"
                            }
                            
                            border {
                                width: {
                                    if (isSelected && !modelData.isToday) return 2
                                    return 0
                                }
                                color: {
                                    if (isSelected && !modelData.isToday) return root.accent
                                    return "transparent"
                                }
                            }
                            visible: modelData.isCurrentMonth && (modelData.isToday || isSelected || isHovered)
                        }

                        // 日期数字
                        Text {
                            id: dayText
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 6
                            
                            text: modelData.day
                            color: {
                                if (!modelData.isCurrentMonth) return Qt.rgba(1, 1, 1, 0.2)
                                if (modelData.isToday) return "#ffffff"
                                if (isSelected) return root.textPrimary
                                if (modelData.isWeekend) return root.weekendColor
                                return root.textPrimary
                            }
                            font.pixelSize: 18
                            font.weight: (modelData.isToday || isSelected) ? 700 : 500

                            Behavior on anchors.topMargin {
                                NumberAnimation { duration: 100; easing.type: Easing.OutCubic }
                            }
                        }

                        // 节假日假期标识 "休"
                        Rectangle {
                            id: holidayTag
                            anchors.left: dayText.right
                            anchors.leftMargin: 2
                            anchors.bottom: dayText.top
                            anchors.bottomMargin: -2
                            width: 18
                            height: 14
                            radius: 3
                            color: root.holidayVacationColor
                            visible: modelData.isHolidayVacation && modelData.isCurrentMonth

                            Text {
                                anchors.centerIn: parent
                                text: "休"
                                color: "#fff"
                                font.pixelSize: 10
                                font.weight: 600
                            }
                        }

                        // 农历/节日/节气（日期下方）
                        Text {
                            id: lunarText
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: dayText.bottom
                            anchors.topMargin: 2
                            text: {
                                if (modelData.festival) return modelData.festival
                                if (modelData.solarTerm) return modelData.solarTerm
                                return modelData.lunar || ""
                            }
                            color: {
                                if (modelData.isToday) return "#dbe6ff"
                                if (isSelected) return root.textSecondary
                                if (modelData.festival) return root.festivalColor
                                if (modelData.solarTerm) return "#f5a623"
                                return root.textTertiary
                            }
                            font.pixelSize: 11
                            font.weight: modelData.festival ? 600 : 400
                            visible: text !== ""
                        }

                        // 事件圆点
                        Rectangle {
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 4
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: 5; height: 5; radius: 2.5
                            color: root.accent
                            visible: modelData.hasEvent
                        }
                    }

                    // 悬停效果
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton
                        
                        onEntered: {
                            if (modelData.isCurrentMonth) {
                                root.hoveredDate = modelData.date
                            }
                        }
                        onExited: {
                            if (root.hoveredDate === modelData.date) {
                                root.hoveredDate = ""
                            }
                        }
                        onClicked: {
                            if (modelData.isCurrentMonth) {
                                root.selectedDate = modelData.date
                                root.dayClicked(modelData.date)
                            }
                        }
                    }
                }
            }
        }

    }
}
