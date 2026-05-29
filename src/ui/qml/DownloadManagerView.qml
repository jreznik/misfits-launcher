import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Item {
    id: downloadRoot
    width: 1280
    height: 800
    focus: true

    Rectangle {
        anchors.fill: parent
        color: "#1a1b26"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 60
        anchors.leftMargin: 60
        anchors.rightMargin: 60
        anchors.bottomMargin: 80
        spacing: 30

        Text {
            text: "DOWNLOAD MANAGER"
            color: "white"
            font.pixelSize: 48
            font.bold: true
        }

        ListView {
            id: downloadList
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20
            model: downloadManager.model
            clip: true
            
            delegate: Rectangle {
                id: downloadDelegate
                width: downloadList.width
                height: 120
                color: activeFocus ? "#2a2a2a" : "#1e1e1e"
                radius: 10
                border.color: activeFocus ? "#3a91f4" : "transparent"
                border.width: 2
                
                // Focus the first button when the row is selected
                onActiveFocusChanged: {
                    if (activeFocus) {
                        pauseBtn.forceActiveFocus()
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 20

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Text {
                            text: model.name
                            color: "white"
                            font.pixelSize: 24
                            font.bold: true
                        }

                        RowLayout {
                            spacing: 20
                            Text {
                                text: model.status.toUpperCase()
                                color: "#3a91f4"
                                font.bold: true
                            }
                            Text {
                                text: model.speed
                                color: "#aaaaaa"
                                visible: model.status === "Downloading"
                            }
                            Text {
                                text: "ETA: " + model.eta
                                color: "#aaaaaa"
                                visible: model.status === "Downloading"
                            }
                        }

                        ProgressBar {
                            Layout.fillWidth: true
                            height: 10
                            value: model.progress / 100.0
                            background: Rectangle { color: "#333"; radius: 5 }
                            contentItem: Item {
                                Rectangle {
                                    width: parent.parent.visualPosition * parent.width
                                    height: parent.height
                                    color: "#3a91f4"
                                    radius: 5
                                }
                            }
                        }
                    }

                    RowLayout {
                        spacing: 10
                        
                        Button {
                            id: pauseBtn
                            text: model.status === "Paused" ? "RESUME" : "PAUSE"
                            visible: model.status === "Downloading" || model.status === "Paused"
                            onClicked: {
                                if (model.status === "Downloading") downloadManager.pause_download(model.appId)
                                else downloadManager.resume_download(model.appId)
                            }
                            KeyNavigation.right: cancelBtn
                            KeyNavigation.up: index > 0 ? downloadList.contentItem.children[index-1] : null
                            KeyNavigation.down: index < downloadList.count - 1 ? downloadList.contentItem.children[index+1] : null
                        }

                        Button {
                            id: cancelBtn
                            text: "CANCEL"
                            visible: model.status !== "Finished"
                            onClicked: downloadManager.cancel_download(model.appId)
                            KeyNavigation.left: pauseBtn.visible ? pauseBtn : null
                            KeyNavigation.right: retryBtn.visible ? retryBtn : removeBtn
                            KeyNavigation.up: index > 0 ? downloadList.contentItem.children[index-1] : null
                            KeyNavigation.down: index < downloadList.count - 1 ? downloadList.contentItem.children[index+1] : null
                        }

                        Button {
                            id: retryBtn
                            text: "RETRY"
                            visible: model.status === "Failed"
                            onClicked: downloadManager.add_to_queue(model.appId, model.name)
                            KeyNavigation.left: cancelBtn
                            KeyNavigation.up: index > 0 ? downloadList.contentItem.children[index-1] : null
                            KeyNavigation.down: index < downloadList.count - 1 ? downloadList.contentItem.children[index+1] : null
                        }
                        
                        Button {
                            id: removeBtn
                            text: "REMOVE"
                            visible: model.status === "Finished" || model.status === "Failed"
                            onClicked: downloadManager.cancel_download(model.appId)
                            KeyNavigation.left: retryBtn.visible ? retryBtn : (cancelBtn.visible ? cancelBtn : null)
                            KeyNavigation.up: index > 0 ? downloadList.contentItem.children[index-1] : null
                            KeyNavigation.down: index < downloadList.count - 1 ? downloadList.contentItem.children[index+1] : null
                        }
                    }
                }
            }
            
            focus: true
        }
    }

    // Bottom Navigation Bar
    Rectangle {
        id: bottomBar
        width: parent.width; height: 80; anchors.bottom: parent.bottom; color: "#1a1b26"; opacity: 0.95
        RowLayout {
            anchors.fill: parent; anchors.leftMargin: 40; anchors.rightMargin: 40
            Item { Layout.fillWidth: true }
            NavigationHints {
                controllerMode: gamepadManager.controllerConnected
                hints: [
                    {key: "Esc", controllerKey: "B", label: "BACK"}
                ]
            }
        }
    }
}
