import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    property string storeName: ""
    property bool isLoggedIn: false
    signal loginRequested()
    signal logoutRequested()

    Layout.fillWidth: true
    height: 80
    color: activeFocus ? "#2a2a2a" : "transparent"
    radius: 8
    border.color: activeFocus ? "#3a91f4" : "transparent"
    border.width: 2
    
    focus: true

    MouseArea {
        anchors.fill: parent
        onClicked: {
            root.forceActiveFocus()
            if (root.isLoggedIn) {
                root.logoutRequested()
            } else {
                root.loginRequested()
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20

        Text {
            text: root.storeName
            color: "white"
            font.pixelSize: 20
            Layout.fillWidth: true
        }

        Rectangle {
            width: 120
            height: 40
            radius: 20
            color: root.isLoggedIn ? "#ff4444" : "#3a91f4"
            
            Text {
                anchors.centerIn: parent
                text: root.isLoggedIn ? "LOGOUT" : "LOGIN"
                color: "white"
                font.bold: true
            }
        }
    }

    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Select || event.key === Qt.Key_Enter) {
            if (root.isLoggedIn) {
                root.logoutRequested()
            } else {
                root.loginRequested()
            }
            event.accepted = true
        }
    }
}
