import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    anchors.fill: parent
    color: "black"
    opacity: 0.85
    visible: false
    z: 250

    property string title: "Confirm"
    property string message: ""
    property string confirmText: "CONFIRM"
    property string cancelText: "CANCEL"
    property bool showStorageOptions: false

    signal confirmed(string installPath)
    signal cancelled()

    property string internalLabel: "Internal"
    property string internalPath: "/"
    property real internalFree: 0
    property real internalTotal: 0
    property string sdLabel: ""
    property string sdPath: ""
    property real sdFree: 0
    property real sdTotal: 0
    property bool sdPresent: false
    property int selectedIndex: -1

    function selectDevice(index) {
        selectedIndex = index
    }

    onVisibleChanged: {
        if (visible) {
            selectedIndex = -1
            if (showStorageOptions) {
                var devices = gameManager.get_storage_info()
                if (devices.length > 0) {
                    internalLabel = devices[0].label
                    internalPath = devices[0].path
                    internalFree = devices[0].free_gb
                    internalTotal = devices[0].total_gb
                    if (devices[0].path === "/")
                        selectedIndex = 0
                }
                if (devices.length > 1) {
                    sdLabel = devices[1].label
                    sdPath = devices[1].path
                    sdFree = devices[1].free_gb
                    sdTotal = devices[1].total_gb
                    sdPresent = true
                    if (selectedIndex < 0)
                        selectedIndex = 1
                }
                if (selectedIndex < 0)
                    selectedIndex = 0
                confirmBtn.forceActiveFocus()
            } else {
                confirmBtn.forceActiveFocus()
            }
        }
    }

    Rectangle {
        id: dialogBox
        anchors.centerIn: parent
        width: 640
        height: showStorageOptions ? 420 : 280
        radius: 8
        color: "#1a1b26"
        border.color: "#3d4450"
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 40
            spacing: 20

            Text {
                text: root.title
                color: "white"
                font.pixelSize: 26
                font.bold: true
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }

            Text {
                text: root.message
                color: "#888888"
                font.pixelSize: 15
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                visible: text !== ""
            }

            Rectangle {
                id: internalCard
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                radius: 6
                visible: showStorageOptions
                color: selectedIndex === 0 ? "#1a3a5c" : "#2a2d38"
                border.color: selectedIndex === 0 ? "#1999ff" : "#3d4450"
                border.width: selectedIndex === 0 ? 2 : 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 20
                    anchors.rightMargin: 20
                    spacing: 10

                    ColumnLayout {
                        spacing: 2
                        Layout.fillWidth: true
                        Text {
                            text: root.internalLabel
                            color: "white"
                            font.pixelSize: 18
                            font.bold: true
                        }
                        Text {
                            text: root.internalPath
                            color: "#888"
                            font.pixelSize: 13
                        }
                    }

                    ColumnLayout {
                        spacing: 2
                        Layout.alignment: Qt.AlignRight
                        Text {
                            text: root.internalFree + " GB free"
                            color: "#4ade80"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        Text {
                            text: "of " + root.internalTotal + " GB"
                            color: "#888"
                            font.pixelSize: 12
                        }
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        root.selectedIndex = 0
                        internalCard.forceActiveFocus()
                    }
                }

                Keys.onPressed: (event) => {
                    if (event.key === Qt.Key_Return || event.key === Qt.Key_Select) {
                        root.selectedIndex = 0
                        event.accepted = true
                    }
                }

                KeyNavigation.down: sdPresent ? sdCard : confirmBtn
                KeyNavigation.tab: sdPresent ? sdCard : confirmBtn
            }

            Rectangle {
                id: sdCard
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                radius: 6
                visible: showStorageOptions && sdPresent
                color: selectedIndex === 1 ? "#1a3a5c" : "#2a2d38"
                border.color: selectedIndex === 1 ? "#1999ff" : "#3d4450"
                border.width: selectedIndex === 1 ? 2 : 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 20
                    anchors.rightMargin: 20
                    spacing: 10

                    ColumnLayout {
                        spacing: 2
                        Layout.fillWidth: true
                        Text {
                            text: root.sdLabel
                            color: "white"
                            font.pixelSize: 18
                            font.bold: true
                        }
                        Text {
                            text: root.sdPath
                            color: "#888"
                            font.pixelSize: 13
                        }
                    }

                    ColumnLayout {
                        spacing: 2
                        Layout.alignment: Qt.AlignRight
                        Text {
                            text: root.sdFree + " GB free"
                            color: "#4ade80"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        Text {
                            text: "of " + root.sdTotal + " GB"
                            color: "#888"
                            font.pixelSize: 12
                        }
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        root.selectedIndex = 1
                        sdCard.forceActiveFocus()
                    }
                }

                Keys.onPressed: (event) => {
                    if (event.key === Qt.Key_Return || event.key === Qt.Key_Select) {
                        root.selectedIndex = 1
                        event.accepted = true
                    }
                }

                KeyNavigation.up: internalCard
                KeyNavigation.down: confirmBtn
                KeyNavigation.tab: confirmBtn
            }

            Item {
                Layout.fillHeight: true
                Layout.maximumHeight: showStorageOptions ? 20 : 9999
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                spacing: 16

                Rectangle {
                    id: cancelBtn
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: activeFocus ? "#1999ff" : "#3d4450"

                    Text {
                        anchors.centerIn: parent
                        text: root.cancelText
                        color: "white"
                        font.bold: true
                        font.pixelSize: 16
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            root.visible = false
                            root.cancelled()
                        }
                    }

                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Select) {
                            root.visible = false
                            root.cancelled()
                            event.accepted = true
                        }
                    }

                    KeyNavigation.right: confirmBtn
                    KeyNavigation.tab: confirmBtn
                    KeyNavigation.up: sdPresent ? sdCard : internalCard
                }

                Rectangle {
                    id: confirmBtn
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: {
                        if (showStorageOptions && root.selectedIndex < 0) return "#555555"
                        return activeFocus ? "#1999ff" : "#3d4450"
                    }

                    Text {
                        anchors.centerIn: parent
                        text: root.confirmText
                        color: (showStorageOptions && root.selectedIndex < 0) ? "#888888" : "white"
                        font.bold: true
                        font.pixelSize: 16
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (showStorageOptions && root.selectedIndex < 0) return
                            root.visible = false
                            var path = ""
                            if (showStorageOptions) {
                                path = root.selectedIndex === 0 ? root.internalPath : root.sdPath
                            }
                            root.confirmed(path)
                        }
                    }

                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Select) {
                            if (showStorageOptions && root.selectedIndex < 0) return
                            root.visible = false
                            var path = ""
                            if (showStorageOptions) {
                                path = root.selectedIndex === 0 ? root.internalPath : root.sdPath
                            }
                            root.confirmed(path)
                            event.accepted = true
                        }
                    }

                    KeyNavigation.left: cancelBtn
                    KeyNavigation.up: sdPresent ? sdCard : internalCard
                    KeyNavigation.tab: internalCard
                    KeyNavigation.backtab: sdPresent ? sdCard : internalCard
                }
            }
        }
    }

    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_Escape || event.key === Qt.Key_Back) {
            root.visible = false
            root.cancelled()
            event.accepted = true
        }
    }
}
