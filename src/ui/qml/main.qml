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

        // Global Navigation
        Keys.onPressed: (event) => {
            console.log("DEBUG: StackView Key pressed:", event.key, "text:", event.text)

            // Standard SteamOS Bumper logic (L1/R1)
            // Support R1, R2, and PageDown for switching to Library
            if (event.key === Qt.Key_PageDown || event.key === Qt.Key_R1 || event.key === Qt.Key_R2) {
                if (mainStack.currentItem.objectName === "homeView") {
                    mainStack.replace(libraryView)
                    event.accepted = true
                }
            } 
            // Support L1, L2, and PageUp for switching back to Home
            else if (event.key === Qt.Key_PageUp || event.key === Qt.Key_L1 || event.key === Qt.Key_L2) {
                if (mainStack.currentItem.objectName === "libraryView") {
                    mainStack.replace(homeView)
                    event.accepted = true
                }
            } else if (event.key === Qt.Key_M || event.key === Qt.Key_Menu) {
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
