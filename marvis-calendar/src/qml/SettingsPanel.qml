import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    ColumnLayout {
        anchors { fill: parent; margins: 16 }
        spacing: 12

        Text {
            text: "设置"
            color: root.parent.parent.textPrimary
            font.pixelSize: 16; font.weight: 700
        }

        // ─── 天气设置 ──────────────────────────────────────────────────
        GroupBox {
            title: "天气"
            Layout.fillWidth: true
            background: Rectangle { color: "transparent"; border { width: 1; color: Qt.rgba(1,1,1,0.06) }; radius: 10 }
            label: Text {
                text: parent.title
                color: root.parent.parent.textSecondary
                font.pixelSize: 11; font.weight: 600
                x: 12; y: -8
            }

            ColumnLayout { spacing: 8; anchors.fill: parent
                Text {
                    text: "当前使用 wttr.in 免费 API，无需 API Key"
                    color: Qt.rgba(0.47, 0.86, 0.47, 0.82)
                    font.pixelSize: 10
                }
                Text {
                    text: "城市名称（英文）"
                    color: root.parent.parent.textTertiary
                    font.pixelSize: 10
                }
                TextField {
                    id: weatherCity
                    Layout.fillWidth: true
                    placeholderText: "Beijing"
                    text: "Beijing"
                    color: root.parent.parent.textPrimary
                    font.pixelSize: 11
                    background: Rectangle {
                        radius: 6; color: Qt.rgba(1,1,1,0.04)
                        border { width: 1; color: Qt.rgba(1,1,1,0.08) }
                    }
                }
                Button {
                    text: "更新天气"
                    background: Rectangle {
                        radius: 6; color: root.parent.parent.accent
                    }
                    contentItem: Text { text: parent.text; color: "#fff"; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                    onClicked: bridge.configure_weather(weatherCity.text)
                }
            }
        }

        // ─── 同步 ──────────────────────────────────────────────────────
        GroupBox {
            title: "WebDAV 同步"
            Layout.fillWidth: true
            background: Rectangle { color: "transparent"; border { width: 1; color: Qt.rgba(1,1,1,0.06) }; radius: 10 }
            label: Text {
                text: parent.title
                color: root.parent.parent.textSecondary
                font.pixelSize: 11; font.weight: 600
                x: 12; y: -8
            }

            ColumnLayout { spacing: 6; anchors.fill: parent
                Text {
                    text: "⚠️ 首版仅支持简单 LWW 同步，多设备同时修改可能丢数据。"
                    color: Qt.rgba(1, 166/255, 35/255, 0.7)
                    font.pixelSize: 9; wrapMode: Text.WordWrap; Layout.fillWidth: true
                }
                TextField { Layout.fillWidth: true; placeholderText: "WebDAV URL"; color: root.parent.parent.textPrimary }
                TextField { Layout.fillWidth: true; placeholderText: "用户名"; color: root.parent.parent.textPrimary }
                TextField { Layout.fillWidth: true; placeholderText: "密码"; echoMode: TextInput.Password; color: root.parent.parent.textPrimary }
            }
        }

        // ─── 关于 ──────────────────────────────────────────────────────
        GroupBox {
            title: "关于"
            Layout.fillWidth: true
            background: Rectangle { color: "transparent"; border { width: 1; color: Qt.rgba(1,1,1,0.06) }; radius: 10 }
            label: Text {
                text: parent.title
                color: root.parent.parent.textSecondary
                font.pixelSize: 11; font.weight: 600
                x: 12; y: -8
            }

            ColumnLayout { spacing: 4; anchors.fill: parent
                Text { text: "鑫哥日历 v0.1.0"; color: root.parent.parent.textPrimary; font.pixelSize: 11 }
                Text { text: "PySide6 + QML · 永久免费 · 无广告"; color: root.parent.parent.textTertiary; font.pixelSize: 9 }
            }
        }
    }
}
