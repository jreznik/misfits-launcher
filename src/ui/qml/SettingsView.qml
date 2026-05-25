import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: settingsRoot
    width: 1280
    height: 800
    focus: true
    objectName: "settingsView"

    property int activeCategoryIndex: 0
    property var categories: [
        {"name": "Accounts", "icon": "👤"},
        {"name": "Runtimes", "icon": "⚙️"}
    ]

    Rectangle {
        anchors.fill: parent
        color: "#0f0f14"
    }

    // Top Bar (Minimal)
    Rectangle {
        id: topBar
        width: parent.width
        height: 80
        color: "transparent"
        z: 10
        RowLayout {
            anchors.fill: parent; anchors.leftMargin: 60; anchors.rightMargin: 60
            Text { text: "SETTINGS"; color: "white"; font.pixelSize: 24; font.bold: true }
            Item { Layout.fillWidth: true }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.topMargin: 80
        anchors.bottomMargin: 80
        spacing: 0

        // Sidebar
        Rectangle {
            Layout.preferredWidth: 350
            Layout.fillHeight: true
            color: "#1a1b26"
            
            ListView {
                id: sidebarList
                anchors.fill: parent
                anchors.topMargin: 40
                model: settingsRoot.categories
                spacing: 0
                clip: true
                focus: true

                delegate: Rectangle {
                    width: parent.width
                    height: 60
                    color: activeFocus ? "#3d4450" : (settingsRoot.activeCategoryIndex === index ? "#2a2b36" : "transparent")
                    
                    RowLayout {
                        anchors.fill: parent; anchors.leftMargin: 30; spacing: 20
                        Text { text: modelData.icon; font.pixelSize: 20 }
                        Text { 
                            text: modelData.name
                            color: "white"; font.pixelSize: 18; font.bold: true
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: { settingsRoot.activeCategoryIndex = index; sidebarList.currentIndex = index; sidebarList.forceActiveFocus() }
                    }

                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_Right) {
                            if (settingsRoot.activeCategoryIndex === 0) epicRow.forceActiveFocus()
                            else umuList.forceActiveFocus()
                            event.accepted = true
                        }
                    }
                }
                
                onCurrentIndexChanged: settingsRoot.activeCategoryIndex = currentIndex
            }
        }

        // Content Area
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#0f0f14"
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 60
                spacing: 40

                Text {
                    text: settingsRoot.categories[settingsRoot.activeCategoryIndex].name
                    color: "white"; font.pixelSize: 36; font.bold: true
                }

                // Accounts View
                ColumnLayout {
                    visible: settingsRoot.activeCategoryIndex === 0
                    Layout.fillWidth: true
                    spacing: 20

                    AccountRow {
                        id: epicRow
                        storeName: "Epic Games"
                        isLoggedIn: accountManager ? accountManager.epicLoggedIn : false
                        onLoginRequested: { loginDialog.targetStore = "Epic"; statusText.text = ""; loginDialog.open() }
                        onLogoutRequested: if (accountManager) accountManager.logout("Epic")
                        KeyNavigation.down: gogRow
                        KeyNavigation.left: sidebarList
                    }

                    ColumnLayout {
                        id: gogRow
                        Layout.fillWidth: true
                        spacing: 5
                        AccountRow {
                            storeName: "GOG"
                            isLoggedIn: false
                            enabled: false
                            opacity: 0.5
                            KeyNavigation.up: epicRow; KeyNavigation.down: amazonRow; KeyNavigation.left: sidebarList
                        }
                        Text { text: "Not supported yet"; color: "#ff4444"; font.pixelSize: 12; font.italic: true; Layout.leftMargin: 20 }
                    }

                    ColumnLayout {
                        id: amazonRow
                        Layout.fillWidth: true
                        spacing: 5
                        AccountRow {
                            storeName: "Amazon Games"
                            isLoggedIn: false
                            enabled: false
                            opacity: 0.5
                            KeyNavigation.up: gogRow; KeyNavigation.left: sidebarList
                        }
                        Text { text: "Not supported yet"; color: "#ff4444"; font.pixelSize: 12; font.italic: true; Layout.leftMargin: 20 }
                    }
                    
                    Item { Layout.fillHeight: true }
                }

                // Runtimes View
                ColumnLayout {
                    visible: settingsRoot.activeCategoryIndex === 1
                    Layout.fillWidth: true
                    spacing: 20

                    Text { id: runtimeStatus; text: ""; color: "#aaaaaa"; font.pixelSize: 14; visible: text !== "" }
                    ProgressBar { id: runtimeProgress; Layout.fillWidth: true; height: 10; visible: value > 0 && value < 1.0; value: 0 }

                    ListView {
                        id: umuList
                        Layout.fillWidth: true; Layout.preferredHeight: 400; spacing: 10; clip: true
                        model: umuManager ? umuManager.runtimes : []
                        delegate: Rectangle {
                            width: umuList.width; height: 60; color: activeFocus ? "#3d4450" : "#1e2129"; radius: 8
                            border.color: activeFocus ? "white" : "transparent"; border.width: 2
                            RowLayout {
                                anchors.fill: parent; anchors.margins: 15
                                Text { text: modelData; color: "white"; font.bold: true; Layout.fillWidth: true }
                                Button { text: "REMOVE"; onClicked: umuManager.remove_runtime(modelData) }
                            }
                            focus: ListView.isCurrentItem
                        }
                        KeyNavigation.left: sidebarList
                        KeyNavigation.down: installBtn
                    }
                    Button {
                        id: installBtn
                        text: "Install Latest GE-Proton"
                        Layout.fillWidth: true
                        onClicked: umuManager.install_latest_ge_proton()
                        KeyNavigation.up: umuList; KeyNavigation.left: sidebarList
                    }
                    Item { Layout.fillHeight: true }
                }
            }
        }
    }

    // Bottom Navigation Bar
    Rectangle {
        id: bottomBar
        width: parent.width; height: 80; anchors.bottom: parent.bottom; color: "#1a1b26"; opacity: 0.95
        RowLayout {
            anchors.fill: parent; anchors.leftMargin: 40; anchors.rightMargin: 40
            Row {
                spacing: 20
                Rectangle { width: 60; height: 30; radius: 15; color: "white"; Text { anchors.centerIn: parent; text: "STEAM"; color: "black"; font.pixelSize: 12; font.bold: true } }
                Text { text: "MENU"; color: "white"; font.pixelSize: 14; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
            }
            Item { Layout.fillWidth: true }
            Row {
                spacing: 30
                Row { spacing: 10
                    Rectangle { width: 24; height: 24; radius: 12; color: "white"; Text { anchors.centerIn: parent; text: "A"; color: "black"; font.bold: true; font.pixelSize: 14 } }
                    Text { text: "SELECT"; color: "white"; font.pixelSize: 14; anchors.verticalCenter: parent.verticalCenter }
                }
                Row { spacing: 10
                    Rectangle { width: 24; height: 24; radius: 12; color: "white"; Text { anchors.centerIn: parent; text: "B"; color: "black"; font.bold: true; font.pixelSize: 14 } }
                    Text { text: "BACK"; color: "white"; font.pixelSize: 14; anchors.verticalCenter: parent.verticalCenter }
                }
            }
        }
    }

    // Login Dialog (Kept from original)
    Dialog {
        id: loginDialog
        anchors.centerIn: parent
        width: 600; height: 500; modal: true; title: "Store Login"
        property string targetStore: ""
        background: Rectangle { color: "#2a2a2a"; radius: 10; border.color: "#3a91f4"; border.width: 2 }
        header: Text { text: " Login to " + loginDialog.targetStore; color: "white"; font.pixelSize: 24; font.bold: true; padding: 20 }
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 20; spacing: 20
            Button { text: "1. Open Login Page"; Layout.fillWidth: true; onClicked: { if (accountManager && loginDialog.targetStore === "Epic") accountManager.trigger_epic_browser() } }
            Rectangle { Layout.fillWidth: true; height: 1; color: "#444" }
            Text { text: "2. Paste Authorization Code"; color: "#3a91f4"; font.pixelSize: 18; font.bold: true }
            TextField { id: tokenField; Layout.fillWidth: true; placeholderText: "Paste code here..."; color: "white"; background: Rectangle { color: "#1a1a1a"; radius: 5; border.color: tokenField.activeFocus ? "#3a91f4" : "#444" } }
            Text { id: statusText; text: ""; color: "#3a91f4"; font.pixelSize: 14; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            Connections { target: accountManager; function onLogin_status_changed(message) { statusText.text = message } }
            RowLayout {
                Layout.alignment: Qt.AlignRight; spacing: 20
                Button { text: "Cancel"; onClicked: loginDialog.close() }
                Button { text: "Login"; highlighted: true; onClicked: { if (accountManager && tokenField.text !== "") accountManager.login(loginDialog.targetStore, tokenField.text, true) } }
            }
        }
    }

    Connections {
        target: umuManager
        function onInstall_progress(progress, status) { runtimeProgress.value = progress / 100.0; runtimeStatus.text = status }
        function onInstall_finished(success, message) { runtimeStatus.text = message; runtimeProgress.value = success ? 1.0 : 0 }
    }
}
