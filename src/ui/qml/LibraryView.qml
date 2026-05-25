import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: libraryRoot
    width: 1280
    height: 800
    focus: true
    
    property int activeFilterIndex: 1
    property var filters: [
        {"name": "GREAT ON DECK"},
        {"name": "ALL GAMES"},
        {"name": "INSTALLED"}
    ]

    property bool showSortMenu: false
    property string backgroundArt: ""
    
    onActiveFocusChanged: {
        if (activeFocus) {
            if (searchField.activeFocus) return;
            libraryGrid.forceActiveFocus()
        }
    }

    // Dynamic Background
    Image {
        id: bgImage
        anchors.fill: parent
        source: libraryRoot.backgroundArt
        fillMode: Image.PreserveAspectCrop
        opacity: 0.3
        asynchronous: true
        
        Behavior on source {
            SequentialAnimation {
                NumberAnimation { target: bgImage; property: "opacity"; to: 0; duration: 200 }
                PropertyAction { target: bgImage; property: "source" }
                NumberAnimation { target: bgImage; property: "opacity"; to: 0.3; duration: 400 }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 1.0; color: "#0f0f14" }
        }
    }

    // Top Bar
    Rectangle {
        id: topBar
        width: parent.width
        height: 80
        color: "transparent"
        z: 10
        
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 40
            anchors.rightMargin: 40
            spacing: 20
            
            Text { text: "Q"; color: "white"; font.pixelSize: 24; font.bold: true }
            
            TextField {
                id: searchField
                Layout.fillWidth: true
                placeholderText: "Search for games..."
                color: "white"
                font.pixelSize: 20
                background: Rectangle {
                    color: searchField.activeFocus ? "#3d4450" : "transparent"
                    radius: 5
                    border.color: searchField.activeFocus ? "#3a91f4" : "transparent"
                    border.width: 2
                }
                onTextChanged: gameManager.search_library(text)
                Keys.onPressed: (event) => {
                    if (event.key === Qt.Key_Down) {
                        filterRepeater.itemAt(activeFilterIndex).forceActiveFocus()
                        event.accepted = true
                    }
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 80
        anchors.bottomMargin: 80
        spacing: 0
        
        Row {
            id: filterRow
            Layout.fillWidth: true
            Layout.leftMargin: 40
            spacing: 20
            
            Repeater {
                id: filterRepeater
                model: libraryRoot.filters
                Rectangle {
                    id: chip
                    width: filterText.width + 40
                    height: 44
                    radius: 22
                    color: libraryRoot.activeFilterIndex === index ? "white" : "transparent"
                    Text {
                        id: filterText
                        anchors.centerIn: parent
                        text: modelData.name
                        color: libraryRoot.activeFilterIndex === index ? "black" : "#aaaaaa"
                        font.pixelSize: 15; font.bold: true
                    }
                    border.color: activeFocus ? (libraryRoot.activeFilterIndex === index ? "#3a91f4" : "white") : "transparent"
                    border.width: 3
                    focus: true
                    
                    // Hardware selection support
                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Select || event.key === Qt.Key_Enter) {
                            libraryRoot.activeFilterIndex = index
                            gameManager.filter_library(modelData.name)
                            event.accepted = true
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            libraryRoot.activeFilterIndex = index
                            gameManager.filter_library(modelData.name)
                            chip.forceActiveFocus()
                        }
                    }
                    KeyNavigation.up: searchField
                    KeyNavigation.down: libraryGrid
                    KeyNavigation.left: index > 0 ? filterRepeater.itemAt(index - 1) : null
                    KeyNavigation.right: index < libraryRoot.filters.length - 1 ? filterRepeater.itemAt(index + 1) : null
                }
            }
        }
        
        GridView {
            id: libraryGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 40
            Layout.rightMargin: 40
            Layout.topMargin: 20
            cellWidth: 235
            cellHeight: 360
            model: gameManager ? gameManager.libraryModel : null
            clip: true
            keyNavigationEnabled: true
            highlightFollowsCurrentItem: true
            focus: true

            onCurrentItemChanged: {
                if (activeFocus && currentItem) {
                    libraryRoot.backgroundArt = currentItem.artwork
                }
            }
            
            onActiveFocusChanged: {
                if (activeFocus && currentItem) {
                    libraryRoot.backgroundArt = currentItem.artwork
                }
            }

            delegate: GameCapsule {
                title: model.name
                artwork: model.artwork
                appId: model.appId
                isInstalled: model.isInstalled
                isNew: index % 4 === 0
                dateLabel: "May 19, 2026"
                compatTier: model.protonTier || ""
                isHero: false
                focus: GridView.isCurrentItem
            }
            KeyNavigation.up: filterRepeater.itemAt(libraryRoot.activeFilterIndex)
        }
    }
    
    // Sort Menu Overlay
    Rectangle {
        visible: showSortMenu
        anchors.fill: parent
        color: "black"
        opacity: 0.9
        z: 200
        ColumnLayout {
            anchors.centerIn: parent
            width: 400
            spacing: 20
            Text { text: "SORT BY"; color: "white"; font.pixelSize: 32; font.bold: true; Layout.alignment: Qt.AlignCenter }
            
            Button { 
                text: "Name (A-Z)"
                Layout.fillWidth: true
                onClicked: { gameManager.set_sort("name", "ASC"); showSortMenu = false }
                focus: showSortMenu
            }
            Button { 
                text: "Name (Z-A)"
                Layout.fillWidth: true
                onClicked: { gameManager.set_sort("name", "DESC"); showSortMenu = false }
            }
            Button { 
                text: "Recently Played"
                Layout.fillWidth: true
                onClicked: { gameManager.set_sort("last_played", "DESC"); showSortMenu = false }
            }
            Button { 
                text: "Date Added"
                Layout.fillWidth: true
                onClicked: { gameManager.set_sort("date_added", "DESC"); showSortMenu = false }
            }
            Button { 
                text: "CANCEL"
                Layout.fillWidth: true
                onClicked: showSortMenu = false
            }
        }
    }

    // Bottom Navigation Bar
    Rectangle {
        id: bottomBar
        width: parent.width
        height: 80
        anchors.bottom: parent.bottom
        color: "#1a1b26"
        opacity: 0.95
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 40
            anchors.rightMargin: 40
            Row {
                spacing: 20
                Rectangle { width: 60; height: 30; radius: 15; color: "white"; Text { anchors.centerIn: parent; text: "STEAM"; color: "black"; font.pixelSize: 12; font.bold: true } }
                Text { text: "MENU"; color: "white"; font.pixelSize: 14; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
            }
            Item { Layout.fillWidth: true }
            Row {
                spacing: 30
                
                Row { spacing: 10
                    Rectangle { width: 24; height: 24; radius: 12; color: "white"; Text { anchors.centerIn: parent; text: "M"; color: "black"; font.bold: true; font.pixelSize: 14 } }
                    Text { text: "SETTINGS"; color: "white"; font.pixelSize: 14; anchors.verticalCenter: parent.verticalCenter }
                }
                Row { spacing: 10
                    Rectangle { width: 24; height: 24; radius: 12; color: "white"; Text { anchors.centerIn: parent; text: "X"; color: "black"; font.bold: true; font.pixelSize: 14 } }
                    Text { text: "FILTER:"; color: "white"; font.pixelSize: 14; anchors.verticalCenter: parent.verticalCenter }
                    Text { text: "✓"; color: "#28a745"; font.pixelSize: 16; anchors.verticalCenter: parent.verticalCenter; font.bold: true }
                }
                Row { spacing: 10
                    Rectangle { width: 24; height: 24; radius: 12; color: "white"; Text { anchors.centerIn: parent; text: "Y"; color: "black"; font.bold: true; font.pixelSize: 14 } }
                    Text { text: "SORT BY"; color: "white"; font.pixelSize: 14; anchors.verticalCenter: parent.verticalCenter }
                }
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

    function cycleFilter(delta) {
        activeFilterIndex = (activeFilterIndex + delta + filters.length) % filters.length
        gameManager.filter_library(filters[activeFilterIndex].name)
    }
    
    Keys.onPressed: (event) => {
        // L1/R1 for tab switching is handled in main.qml
        // L2/R2 for filter cycling
        if (event.key === Qt.Key_BracketLeft || event.key === Qt.Key_L2) {
            cycleFilter(-1); event.accepted = true
        } else if (event.key === Qt.Key_BracketRight || event.key === Qt.Key_R2) {
            cycleFilter(1); event.accepted = true
        } else if (event.key === Qt.Key_Y || event.key === Qt.Key_Menu) {
            showSortMenu = !showSortMenu
            event.accepted = true
        } else if (event.key === Qt.Key_X) {
            cycleFilter(1)
            event.accepted = true
        }
    }
}
