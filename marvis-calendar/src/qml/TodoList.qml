import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property var todos: ([])

    function refresh() { todos = bridge.all_todos() }
    Component.onCompleted: refresh()

    ColumnLayout {
        anchors { fill: parent; margins: 12 }
        spacing: 6

        Text {
            text: "待办清单"
            color: root.parent.parent.textPrimary
            font.pixelSize: 16; font.weight: 700
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: todos
            spacing: 5
            clip: true

            delegate: Rectangle {
                width: ListView.view.width; height: 44; radius: 8
                color: Qt.rgba(1,1,1,0.025)
                border { width: 1; color: Qt.rgba(1,1,1,0.05) }

                RowLayout {
                    anchors { fill: parent; margins: 8 }
                    spacing: 8

                    // 勾选框
                    Rectangle {
                        width: 18; height: 18; radius: 9
                        color: modelData.completed ? root.parent.parent.accent : "transparent"
                        border { width: 1.5; color: modelData.completed ? root.parent.parent.accent : Qt.rgba(1,1,1,0.2) }
                        Layout.alignment: Qt.AlignVCenter
                        Text {
                            anchors.centerIn: parent
                            text: modelData.completed ? "✓" : ""
                            color: "#fff"; font.pixelSize: 11
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                bridge.toggle_todo(modelData.id, !modelData.completed)
                                root.refresh()
                            }
                        }
                    }

                    ColumnLayout { spacing: 0
                        Layout.fillWidth: true
                        Text {
                            text: modelData.title
                            color: modelData.completed ? root.parent.parent.textTertiary : root.parent.parent.textPrimary
                            font.pixelSize: 12
                            font.strikeout: modelData.completed
                        }
                        Text {
                            text: modelData.due_date || ""
                            color: root.parent.parent.textTertiary
                            font.pixelSize: 9
                            visible: modelData.due_date ? true : false
                        }
                    }

                    // 优先级指示
                    Rectangle {
                        width: 8; height: 8; radius: 4
                        color: {
                            switch(modelData.priority) {
                                case 3: return "#ff6b6b"
                                case 2: return "#f5a623"
                                default: return Qt.rgba(1,1,1,0.2)
                            }
                        }
                        Layout.alignment: Qt.AlignVCenter
                    }
                }
            }
        }

        // 添加待办
        Rectangle {
            Layout.fillWidth: true; height: 32; radius: 8
            color: Qt.rgba(94/255, 140/255, 240/255, 0.06)
            border { width: 1; color: Qt.rgba(94/255, 140/255, 240/255, 0.15) }
            Text {
                anchors.centerIn: parent
                text: "+ 添加待办"
                color: Qt.rgba(94/255, 140/255, 240/255, 0.65)
                font.pixelSize: 10
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {} // TODO
            }
        }
    }
}
