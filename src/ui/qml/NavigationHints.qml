import QtQuick 2.15
import QtQuick.Layouts 1.15

Row {
    id: root
    spacing: 30
    anchors.bottom: parent.bottom
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottomMargin: 20

    property var hints: [
        {"key": "L1/R1", "label": "Switch Tabs"},
        {"key": "M", "label": "Settings"},
        {"key": "A", "label": "Launch"}
    ]

    Repeater {
        model: root.hints
        Row {
            spacing: 10
            Rectangle {
                width: 40
                height: 40
                radius: 20
                color: "#3a91f4"
                Text {
                    anchors.centerIn: parent
                    text: modelData.key
                    color: "white"
                    font.bold: true
                    font.pixelSize: 14
                }
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: modelData.label
                color: "#aaaaaa"
                font.pixelSize: 16
            }
        }
    }
}
