import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Item {
    id: homeRoot
    width: 1280
    height: 800
    focus: true

    property string backgroundArt: ""
    
    // Hardened focus handoff
    onActiveFocusChanged: {
        if (activeFocus) {
            recentAllShelf.forceActiveFocus()
        }
    }

    // Dynamic Background
    Image {
        id: bgImage
        anchors.fill: parent
        source: homeRoot.backgroundArt
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

    Column {
        anchors.fill: parent
        anchors.margins: 40
        spacing: 40
        
        Text {
            text: "Home"
            color: "white"
            font.pixelSize: 48
            font.bold: true
        }
        
        // Shelf: Recently Played + Recently Added (merged like Steam Deck)
        Column {
            width: parent.width
            spacing: 20
            
            Text {
                text: "RECENT"
                color: "#aaaaaa"
                font.pixelSize: 18
                font.letterSpacing: 2
            }
            
            ListView {
                id: recentAllShelf
                width: parent.width
                height: 360
                orientation: ListView.Horizontal
                spacing: 20
                model: gameManager ? gameManager.recentAllModel : null
                clip: false
                
                keyNavigationEnabled: true
                highlightFollowsCurrentItem: true
                focus: true

                onCurrentItemChanged: {
                    if (currentItem) {
                        homeRoot.backgroundArt = currentItem.artwork
                    }
                }
                
                onActiveFocusChanged: {
                    if (activeFocus && currentItem) {
                        homeRoot.backgroundArt = currentItem.artwork
                    }
                }

                delegate: GameCapsule {
                    title: model.name
                    artwork: model.artwork
                    appId: model.appId
                    isInstalled: model.isInstalled
                    isNew: model.isNew
                    isHero: index === 0
                    showTitle: true
                    dateLabel: model.isNew && model.installTimestamp > 0 ? new Date(model.installTimestamp * 1000).toLocaleDateString(undefined, {year: 'numeric', month: 'short', day: 'numeric'}) : ""
                    focus: ListView.isCurrentItem
                }
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
            Item { Layout.fillWidth: true }
            NavigationHints {
                controllerMode: gamepadManager.controllerConnected
                hints: [
                    {key: "M", controllerKey: "Options", label: "SETTINGS"},
                    {key: "D", label: "DOWNLOADS"},
                    {key: "Enter", controllerKey: "A", label: "DETAILS"}
                ]
            }
        }
    }
}
