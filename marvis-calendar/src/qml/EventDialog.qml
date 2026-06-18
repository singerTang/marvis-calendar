import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 日程编辑对话框：modal 弹窗，内部直接调用全局 bridge 完成增删改
Popup {
    id: root

    // ─── 对外 API ─────────────────────────────────────────────────────
    property string mode: "create"      // "create" | "edit"
    property string targetDate: ""      // "YYYY-MM-DD"，新增时所属日期
    property var eventData: null        // 编辑模式传入的现有事件 dict

    // ─── 颜色 Token（按项目约定在 root 内重新声明，不用 parent 引用链）────
    readonly property color accent: "#5e8cf0"
    readonly property color cardBg: Qt.rgba(0.08, 0.08, 0.1, 0.98)
    readonly property color cardBorder: Qt.rgba(1, 1, 1, 0.08)
    readonly property color textPrimary: Qt.rgba(1, 1, 1, 0.95)
    readonly property color textSecondary: Qt.rgba(1, 1, 1, 0.75)
    readonly property color textTertiary: Qt.rgba(1, 1, 1, 0.52)
    readonly property color fieldBg: Qt.rgba(1, 1, 1, 0.04)
    readonly property color dangerColor: "#f0815e"

    // ─── 预设值 ───────────────────────────────────────────────────────
    // 提醒选项文案与 reminder_minutes 一一对应，索引即映射
    readonly property var reminderLabels: ["不提醒", "准时", "提前5分钟", "提前15分钟", "提前30分钟", "提前1小时", "提前1天"]
    readonly property var reminderValues: [-1, 0, 5, 15, 30, 60, 1440]
    readonly property var presetColors: ["#5e8cf0", "#f0815e", "#5ef0a0", "#f05e8c", "#c05ef0", "#f0d65e"]

    // ─── 内部状态 ─────────────────────────────────────────────────────
    property int selectedColorIndex: 0
    property string errorText: ""
    property bool confirmingDelete: false   // 删除二次确认状态

    // ─── 弹窗基础配置 ─────────────────────────────────────────────────
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    width: 360
    // 居中于父级（Overlay）
    anchors.centerIn: Overlay.overlay
    padding: 0

    background: Rectangle {
        radius: 14
        color: root.cardBg
        border { width: 1; color: root.cardBorder }
    }

    Overlay.modal: Rectangle {
        color: Qt.rgba(0, 0, 0, 0.5)
    }

    // ─── 对外方法 ─────────────────────────────────────────────────────
    // 重置为新增模式并打开
    function openCreate(dateStr) {
        mode = "create"
        targetDate = dateStr || ""
        eventData = null
        resetForm()
        open()
    }

    // 载入现有事件到表单，切换编辑模式并打开
    function openEdit(ev) {
        mode = "edit"
        eventData = ev
        targetDate = (ev && ev.date) ? ev.date : ""
        loadFromEvent(ev)
        open()
    }

    // ─── 内部辅助 ─────────────────────────────────────────────────────
    // 重置表单为默认值
    function resetForm() {
        titleField.text = ""
        allDaySwitch.checked = false
        startField.text = "09:00"
        endField.text = "10:00"
        reminderCombo.currentIndex = 0
        selectedColorIndex = 0
        notesArea.text = ""
        errorText = ""
        confirmingDelete = false
    }

    // 把事件字段回填到表单，缺失字段以默认值兜底（稳健优先）
    function loadFromEvent(ev) {
        resetForm()
        if (!ev) return

        titleField.text = ev.title || ""
        notesArea.text = ev.notes || ""
        allDaySwitch.checked = ev.all_day === true

        // 时间回填：信任 event_for_edit 提供的结构化 start_hhmm/end_hhmm，
        // 缺失或全天（为空串）时保留 resetForm 的默认值
        var re = /^\d{2}:\d{2}$/
        if (re.test(ev.start_hhmm || "")) startField.text = ev.start_hhmm
        if (re.test(ev.end_hhmm || "")) endField.text = ev.end_hhmm

        // 颜色回填：在预设中查找匹配项，找不到则默认第 0 个
        if (ev.color) {
            var idx = presetColors.indexOf(ev.color)
            selectedColorIndex = idx >= 0 ? idx : 0
        }

        // 提醒回填：按 reminder_minutes 反查索引，找不到则“不提醒”
        if (ev.reminder_minutes !== undefined && ev.reminder_minutes !== null) {
            var rIdx = reminderValues.indexOf(ev.reminder_minutes)
            reminderCombo.currentIndex = rIdx >= 0 ? rIdx : 0
        }
    }

    // 校验 HH:MM 格式
    function isValidTime(t) {
        if (!/^\d{2}:\d{2}$/.test(t)) return false
        var h = parseInt(t.substring(0, 2), 10)
        var m = parseInt(t.substring(3, 5), 10)
        return h >= 0 && h <= 23 && m >= 0 && m <= 59
    }

    // 标题非空即可保存
    readonly property bool canSave: titleField.text.trim().length > 0

    // 保存：组装 data 调用 bridge，失败显示错误文案不关闭，成功则关闭
    function doSave() {
        errorText = ""
        if (!canSave) {
            errorText = "请输入日程标题"
            return
        }

        var allDay = allDaySwitch.checked
        // 非全天才校验时间
        if (!allDay) {
            if (!isValidTime(startField.text) || !isValidTime(endField.text)) {
                errorText = "时间格式应为 HH:MM"
                return
            }
        }

        var data = {
            "date": targetDate,
            "all_day": allDay,
            "start_hhmm": allDay ? "" : startField.text,
            "end_hhmm": allDay ? "" : endField.text,
            "title": titleField.text.trim(),
            "notes": notesArea.text,
            "color": presetColors[selectedColorIndex],
            "reminder_minutes": reminderValues[reminderCombo.currentIndex]
        }

        var res
        if (mode === "edit" && eventData && eventData.id !== undefined) {
            res = bridge.update_event(eventData.id, data)
        } else {
            res = bridge.add_event(data)
        }

        if (res && res.ok) {
            close()
        } else {
            errorText = (res && res.error) ? res.error : "保存失败"
        }
    }

    // 删除：二次确认后调用 bridge.delete_event
    function doDelete() {
        if (!confirmingDelete) {
            confirmingDelete = true
            return
        }
        if (eventData && eventData.id !== undefined) {
            var ok = bridge.delete_event(eventData.id)
            if (ok) {
                close()
            } else {
                errorText = "删除失败"
                confirmingDelete = false
            }
        }
    }

    onClosed: confirmingDelete = false

    // ─── 内容布局 ─────────────────────────────────────────────────────
    contentItem: ColumnLayout {
        spacing: 12

        // 标题栏
        Text {
            Layout.fillWidth: true
            Layout.topMargin: 16
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            text: root.mode === "edit" ? "编辑日程" : "新建日程"
            color: root.textPrimary
            font.pixelSize: 16
            font.weight: 700
        }

        // 表单滚动区
        ScrollView {
            Layout.fillWidth: true
            Layout.preferredHeight: contentColumn.implicitHeight
            Layout.maximumHeight: 420
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: contentColumn
                width: parent.width
                spacing: 12

                // 1. 标题
                TextField {
                    id: titleField
                    Layout.fillWidth: true
                    placeholderText: "日程标题"
                    color: root.textPrimary
                    placeholderTextColor: root.textTertiary
                    font.pixelSize: 13
                    selectByMouse: true
                    background: Rectangle {
                        radius: 8
                        color: root.fieldBg
                        border { width: 1; color: titleField.activeFocus ? root.accent : root.cardBorder }
                    }
                }

                // 2. 全天
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "全天"
                        color: root.textSecondary
                        font.pixelSize: 12
                        Layout.fillWidth: true
                    }
                    Switch {
                        id: allDaySwitch
                        checked: false
                    }
                }

                // 3. 开始/结束时间（全天时隐藏）
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    visible: !allDaySwitch.checked

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text { text: "开始"; color: root.textTertiary; font.pixelSize: 11 }
                        TextField {
                            id: startField
                            Layout.fillWidth: true
                            placeholderText: "HH:MM"
                            inputMask: "99:99"
                            text: "09:00"
                            color: root.textPrimary
                            placeholderTextColor: root.textTertiary
                            font.pixelSize: 13
                            background: Rectangle {
                                radius: 8
                                color: root.fieldBg
                                border { width: 1; color: startField.activeFocus ? root.accent : root.cardBorder }
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text { text: "结束"; color: root.textTertiary; font.pixelSize: 11 }
                        TextField {
                            id: endField
                            Layout.fillWidth: true
                            placeholderText: "HH:MM"
                            inputMask: "99:99"
                            text: "10:00"
                            color: root.textPrimary
                            placeholderTextColor: root.textTertiary
                            font.pixelSize: 13
                            background: Rectangle {
                                radius: 8
                                color: root.fieldBg
                                border { width: 1; color: endField.activeFocus ? root.accent : root.cardBorder }
                            }
                        }
                    }
                }

                // 4. 提醒
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Text { text: "提醒"; color: root.textTertiary; font.pixelSize: 11 }
                    ComboBox {
                        id: reminderCombo
                        Layout.fillWidth: true
                        model: root.reminderLabels
                        currentIndex: 0
                        font.pixelSize: 13
                        // 选中项文字
                        contentItem: Text {
                            leftPadding: 10
                            text: reminderCombo.displayText
                            color: root.textPrimary
                            font.pixelSize: 13
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                        background: Rectangle {
                            radius: 8
                            color: root.fieldBg
                            border { width: 1; color: root.cardBorder }
                        }
                        delegate: ItemDelegate {
                            width: reminderCombo.width
                            contentItem: Text {
                                text: modelData
                                color: root.textPrimary
                                font.pixelSize: 13
                                verticalAlignment: Text.AlignVCenter
                            }
                            highlighted: reminderCombo.highlightedIndex === index
                            background: Rectangle {
                                color: highlighted ? Qt.rgba(0.37, 0.55, 0.94, 0.15) : "transparent"
                            }
                        }
                        popup: Popup {
                            y: reminderCombo.height + 2
                            width: reminderCombo.width
                            implicitHeight: contentItem.implicitHeight
                            padding: 4
                            contentItem: ListView {
                                clip: true
                                implicitHeight: contentHeight
                                model: reminderCombo.popup.visible ? reminderCombo.delegateModel : null
                                currentIndex: reminderCombo.highlightedIndex
                                ScrollIndicator.vertical: ScrollIndicator {}
                            }
                            background: Rectangle {
                                radius: 8
                                color: root.cardBg
                                border { width: 1; color: root.cardBorder }
                            }
                        }
                    }
                }

                // 5. 颜色
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Text { text: "颜色"; color: root.textTertiary; font.pixelSize: 11 }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Repeater {
                            model: root.presetColors
                            Rectangle {
                                width: 28; height: 28; radius: 14
                                color: modelData
                                border {
                                    width: root.selectedColorIndex === index ? 2 : 0
                                    color: root.textPrimary
                                }
                                // 选中高亮外圈
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: parent.width + 8; height: parent.height + 8
                                    radius: width / 2
                                    color: "transparent"
                                    border {
                                        width: root.selectedColorIndex === index ? 1 : 0
                                        color: root.accent
                                    }
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.selectedColorIndex = index
                                }
                            }
                        }
                    }
                }

                // 6. 备注
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Text { text: "备注"; color: root.textTertiary; font.pixelSize: 11 }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 72
                        radius: 8
                        color: root.fieldBg
                        border { width: 1; color: notesArea.activeFocus ? root.accent : root.cardBorder }
                        ScrollView {
                            anchors.fill: parent
                            anchors.margins: 6
                            clip: true
                            TextArea {
                                id: notesArea
                                placeholderText: "备注（可选）"
                                color: root.textPrimary
                                placeholderTextColor: root.textTertiary
                                font.pixelSize: 12
                                wrapMode: TextArea.Wrap
                                selectByMouse: true
                                background: null
                            }
                        }
                    }
                }
            }
        }

        // 错误提示（红色小字）
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            visible: root.errorText.length > 0
            text: root.errorText
            color: root.dangerColor
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }

        // ─── 底部按钮 ─────────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Layout.bottomMargin: 16
            spacing: 10

            // 删除按钮：仅编辑模式显示，靠左
            Button {
                id: deleteBtn
                visible: root.mode === "edit"
                text: root.confirmingDelete ? "确认删除？" : "删除"
                font.pixelSize: 12
                implicitHeight: 34
                onClicked: root.doDelete()
                contentItem: Text {
                    text: deleteBtn.text
                    color: root.dangerColor
                    font.pixelSize: 12
                    font.weight: 500
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 8
                    implicitWidth: 80
                    color: root.confirmingDelete ? Qt.rgba(0.94, 0.51, 0.37, 0.18) : Qt.rgba(0.94, 0.51, 0.37, 0.08)
                    border { width: 1; color: Qt.rgba(0.94, 0.51, 0.37, 0.3) }
                }
            }

            Item { Layout.fillWidth: true }

            // 取消
            Button {
                id: cancelBtn
                text: "取消"
                font.pixelSize: 12
                implicitHeight: 34
                onClicked: root.close()
                contentItem: Text {
                    text: cancelBtn.text
                    color: root.textSecondary
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 8
                    implicitWidth: 72
                    color: Qt.rgba(1, 1, 1, 0.04)
                    border { width: 1; color: root.cardBorder }
                }
            }

            // 保存
            Button {
                id: saveBtn
                text: "保存"
                font.pixelSize: 12
                implicitHeight: 34
                enabled: root.canSave
                onClicked: root.doSave()
                contentItem: Text {
                    text: saveBtn.text
                    color: root.textPrimary
                    font.pixelSize: 12
                    font.weight: 600
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 8
                    implicitWidth: 72
                    color: saveBtn.enabled ? root.accent : Qt.rgba(0.37, 0.55, 0.94, 0.3)
                    opacity: saveBtn.enabled ? 1.0 : 0.6
                }
            }
        }
    }
}
