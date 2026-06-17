import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    property int currentIndex: 0
    signal tabClicked(int index)

    // 颜色由父级传入
    property color accent: "#5e8cf0"
    property color textPrimary: Qt.rgba(1, 1, 1, 0.95)
    property color textTertiary: Qt.rgba(1, 1, 1, 0.52)

    Rectangle {
        anchors.fill: parent
        color: "transparent"
        border { width: 1; color: Qt.rgba(1,1,1,0.05) }

        RowLayout {
            anchors.fill: parent
            anchors.margins: 6
            spacing: 0

            Repeater {
                model: [
                    { label: "月历", icon: "☾" },
                    { label: "周历", icon: "◷" },
                    { label: "日历", icon: "☀" },
                    { label: "待办", icon: "☑" }
                ]
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    property bool isActive: index === root.currentIndex

                    Rectangle {
                        anchors { fill: parent; margins: 2 }
                        radius: 10
                        color: isActive ? Qt.rgba(0.37, 0.55, 0.94, 0.06) : "transparent"

                        // 激活态底部指示条
                        Rectangle {
                            anchors { bottom: parent.bottom; bottomMargin: 4; horizontalCenter: parent.horizontalCenter }
                            width: isActive ? 16 : 0; height: 2.5; radius: 1.5
                            color: root.accent
                            Behavior on width { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
                        }

                        Behavior on color { ColorAnimation { duration: 250 } }
                    }

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 2

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: modelData.icon
                            color: isActive ? root.accent : root.textTertiary
                            font.pixelSize: 16
                            Behavior on color { ColorAnimation { duration: 250 } }
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: modelData.label
                            color: isActive ? root.accent : root.textTertiary
                            font.pixelSize: 10; font.weight: isActive ? 600 : 400
                            Behavior on color { ColorAnimation { duration: 250 } }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (!isActive) root.tabClicked(index)
                        }
                    }
                }
            }
        }
    }
}
