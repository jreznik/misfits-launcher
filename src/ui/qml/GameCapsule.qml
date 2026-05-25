import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    property string title: ""
    property string artwork: ""
    property string appId: ""
    property bool isHero: false
    property bool isInstalled: true
    property bool isNew: false
    property string dateLabel: ""
    property string compatTier: "" // platinum, gold, etc
    
    width: isHero ? 400 : 215
    height: isHero ? 225 : 340
    
    scale: activeFocus ? 1.05 : 1.0
    z: activeFocus ? 10 : 1
    
    Behavior on scale { NumberAnimation { duration: 150 } }

    Column {
        anchors.fill: parent
        spacing: 8

        Rectangle {
            id: posterContainer
            width: parent.width
            height: isHero ? parent.height : 310
            color: "#2a2a2a"
            radius: 4
            clip: true
            
            border.color: root.activeFocus ? "white" : "transparent"
            border.width: 4

            Image {
                id: mainImage
                anchors.fill: parent
                source: root.artwork
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                cache: true
                opacity: 1.0
            }

            
            // Placeholder Title (Visible if image is loading or fails)
            Text {
                visible: mainImage.status !== Image.Ready
                anchors.centerIn: parent
                anchors.margins: 20
                width: parent.width - 40
                text: root.title
                color: "#555"
                font.pixelSize: 18
                font.bold: true
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                maximumLineCount: 3
            }

            // Loading indicator for image
            BusyIndicator {
                anchors.centerIn: parent
                running: mainImage.status === Image.Loading
                visible: running
                scale: 0.5
            }

            // "NEW TO LIBRARY" Banner
            Rectangle {
                visible: root.isNew
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.topMargin: 10
                anchors.leftMargin: 10
                width: 100
                height: 22
                color: "#3a91f4"
                Text {
                    anchors.centerIn: parent
                    text: "NEW TO LIBRARY"
                    color: "white"
                    font.pixelSize: 10
                    font.bold: true
                }
            }

            // Compatibility Icons
            Row {
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.margins: 8
                spacing: 4
                visible: root.compatTier !== ""

                Rectangle {
                    width: 24
                    height: 24
                    radius: 12
                    color: root.compatTier === "platinum" ? "#b4b4b4" : "#cfb53b"
                    visible: root.compatTier === "platinum" || root.compatTier === "gold"
                    Text {
                        anchors.centerIn: parent
                        text: "✓"
                        color: "white"
                        font.bold: true
                    }
                }
            }
        }

        Text {
            visible: !isHero
            width: parent.width
            text: root.dateLabel || "May 19, 2026"
            color: "#888888"
            font.pixelSize: 14
            horizontalAlignment: Text.AlignHCenter
        }
    }
    
    MouseArea {
        anchors.fill: parent
        onClicked: {
            root.forceActiveFocus()
            mainStack.push(detailView, {"appId": root.appId})
        }
    }

    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Select || event.key === Qt.Key_Enter) {
            mainStack.push(detailView, {"appId": root.appId})
            event.accepted = true
        }
    }
}
