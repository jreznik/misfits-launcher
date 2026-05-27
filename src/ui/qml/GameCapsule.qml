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
    property bool showTitle: false
    
    width: isHero ? 400 : 215
    height: 360

    readonly property bool _selected: activeFocus || (typeof ListView !== 'undefined' && ListView.isCurrentItem)
    property bool _pulsing: true

    scale: _selected ? 1.05 : 1.0
    z: _selected ? 10 : 1
    
    Behavior on scale { NumberAnimation { duration: 150 } }

    Timer {
        id: idleTimer
        interval: 60000
        onTriggered: {
            root._pulsing = false
            focusFrame.opacity = 1.0
        }
    }

    on_SelectedChanged: {
        if (_selected) {
            root._pulsing = true
            idleTimer.restart()
        }
    }

    Column {
        anchors.fill: parent
        spacing: 6

        Item {
            width: parent.width
            height: 310

            // Focus frame (behind poster, spaced a few pixels out)
            Rectangle {
                id: focusFrame
                anchors.centerIn: parent
                width: parent.width + 8
                height: parent.height + 8
                radius: 0
                color: "transparent"
                border.color: "#b0b8c0"
                border.width: 0
                visible: root._selected

                states: State {
                    name: "focused"
                    when: root._selected
                    PropertyChanges { target: focusFrame; border.width: 2 }
                }

                transitions: [
                    Transition {
                        from: ""; to: "focused"
                        SequentialAnimation {
                            PropertyAction { property: "opacity"; value: 1.0 }
                            PropertyAction { property: "border.width"; value: 6 }
                            PauseAnimation { duration: 16 }
                            NumberAnimation { property: "border.width"; to: 2; duration: 200; easing.type: Easing.OutQuad }
                        }
                    },
                    Transition {
                        from: "focused"; to: ""
                        ParallelAnimation {
                            NumberAnimation { property: "border.width"; to: 0; duration: 100 }
                            NumberAnimation { property: "opacity"; to: 0.0; duration: 100 }
                        }
                    }
                ]

                // Pulsing opacity between 30% and 100%
                SequentialAnimation on opacity {
                    loops: Animation.Infinite
                    running: root._selected && root._pulsing
                    PropertyAnimation { to: 0.3; duration: 900; easing.type: Easing.InOutSine }
                    PropertyAnimation { to: 1.0; duration: 900; easing.type: Easing.InOutSine }
                }
            }

            Rectangle {
                id: posterContainer
                anchors.fill: parent
                color: "#2a2a2a"
                radius: 4
                clip: true

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
        }

        // Game name (only visible for the selected/focused game)
        Text {
            width: parent.width
            visible: root._selected && root.showTitle
            text: root.title
            color: "white"
            font.pixelSize: root.isHero ? 22 : 18
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
            maximumLineCount: 1
        }

        Text {
            visible: !isHero && root.dateLabel !== ""
            width: parent.width
            text: root.dateLabel || ""
            color: "#888888"
            font.pixelSize: 13
            horizontalAlignment: Text.AlignHCenter
        }
    }
    
    MouseArea {
        anchors.fill: parent
        onClicked: {
            idleTimer.restart()
            if (!root._pulsing && root._selected) {
                root._pulsing = true
                focusFrame.opacity = 1.0
            }
            root.forceActiveFocus()
            mainStack.push(detailView, {"appId": root.appId})
        }
    }

    Keys.onPressed: (event) => {
        idleTimer.restart()
        if (!root._pulsing && root._selected) {
            root._pulsing = true
            focusFrame.opacity = 1.0
        }
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Select || event.key === Qt.Key_Enter) {
            mainStack.push(detailView, {"appId": root.appId})
            event.accepted = true
        }
    }
}
