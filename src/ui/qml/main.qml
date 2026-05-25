import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    id: window
    width: 1280
    height: 800
    visible: true
    title: "MisfitsLauncher"
    color: "#1a1a1a"
    // Main Background

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#1a1b26" }
            GradientStop { position: 1.0; color: "#0f0f14" }
        }
    }
    StackView {
        id: mainStack
        anchors.fill: parent
        initialItem: homeView
        focus: true

        onCurrentItemChanged: {
            if (currentItem) {
                console.log("DEBUG: Screen changed to:", currentItem.objectName)
                currentItem.forceActiveFocus()
            }
        }

        // Catches keyboard PgUp/PgDown delivered directly when StackView has focus
        Keys.onPressed: (event) => {
            if (event.key === Qt.Key_PageDown) {
                if (mainStack.currentItem.objectName === "homeView") {
                    mainStack.replace(libraryView)
                    event.accepted = true
                }
            } else if (event.key === Qt.Key_PageUp) {
                if (mainStack.currentItem.objectName === "libraryView") {
                    mainStack.replace(homeView)
                    event.accepted = true
                }
            }
        }
    }

    // Keyboard shortcuts (these work via OS key delivery to focused items)
    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_M || event.key === Qt.Key_Menu) {
            if (mainStack.currentItem.objectName !== "settingsView") {
                mainStack.push(settingsView)
                event.accepted = true
            }
        } else if (event.key === Qt.Key_D) {
            if (mainStack.currentItem.objectName !== "downloadView") {
                mainStack.push(downloadView)
                event.accepted = true
            }
        } else if (event.key === Qt.Key_Escape || event.key === Qt.Key_B) {
            if (mainStack.depth > 1) {
                mainStack.pop()
                event.accepted = true
            }
        }
    }

    // Controller global actions — delivered via Qt signals, bypasses key routing
    Connections {
        target: gamepadManager
        function onL1Pressed() {
            if (mainStack.currentItem.objectName === "libraryView")
                mainStack.replace(homeView)
        }
        function onR1Pressed() {
            if (mainStack.currentItem.objectName === "homeView")
                mainStack.replace(libraryView)
        }
        function onBackPressed() {
            if (mainStack.depth > 1)
                mainStack.pop()
        }
        function onMenuPressed() {
            if (mainStack.currentItem.objectName !== "settingsView")
                mainStack.push(settingsView)
        }
    }
    
    Component {
        id: homeView
        HomeView { objectName: "homeView" }
    }
    
    Component {
        id: libraryView
        LibraryView { objectName: "libraryView" }
    }

    Component {
        id: settingsView
        SettingsView { objectName: "settingsView" }
    }

    Component {
        id: detailView
        GameDetailView { objectName: "detailView" }
    }

    Component {
        id: downloadView
        DownloadManagerView { objectName: "downloadView" }
    }
}
