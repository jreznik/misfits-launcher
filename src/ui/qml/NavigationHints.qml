import QtQuick 2.15
import QtQuick.Layouts 1.15

Row {
    id: root
    spacing: 30

    property bool controllerMode: false
    property var hints: []

    function resolveKey(hint) {
        if (root.controllerMode && hint.controllerKey)
            return hint.controllerKey
        var k = hint.key
        if (k === "Enter") return "\u21B5"
        return k
    }

    function pillWidth(hint) {
        var text = resolveKey(hint)
        if (text.length <= 1) return 24
        return Math.max(24, text.length * 9 + 12)
    }

    Repeater {
        model: root.hints
        Row {
            spacing: 10
            Rectangle {
                width: pillWidth(modelData)
                height: 24
                radius: 12
                color: "white"
                Text {
                    id: keyText
                    anchors.centerIn: parent
                    text: resolveKey(modelData)
                    color: "black"
                    font.bold: true
                    font.pixelSize: 14
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: modelData.label
                color: "white"
                font.pixelSize: 14
            }
        }
    }
}
