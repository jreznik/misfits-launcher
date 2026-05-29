import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Item {
    id: detailRoot
    width: 1280
    height: 800
    focus: true

    property var gameData: null
    property string appId: ""
    property string launchStatus: ""
    property bool isLaunching: false

    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_Escape || event.key === Qt.Key_B) {
            mainStack.pop()
            event.accepted = true
        }
    }
    property real installProgress: 0
    property string installStatus: ""
    property bool isInstalling: false
    property bool isLoading: true
    property bool isDownloading: false
    property string downloadSpeed: ""
    property string downloadEta: ""
    
    // Reactive properties
    property string gameDescription: ""
    property string lastPlayedText: "Never"
    property string gameSizeText: ""

    // Force re-check when returning to this view
    onVisibleChanged: { if (visible) checkDownloadStatus() }
    onActiveFocusChanged: { if (activeFocus) checkDownloadStatus() }

    // Background Hero Art
    Image {
        id: heroArt
        anchors.fill: parent
        source: (gameData && gameData.hero) ? gameData.hero : ""
        fillMode: Image.PreserveAspectCrop
        opacity: 0.3
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 0.4; color: "transparent" }
            GradientStop { position: 1.0; color: "#0f0f14" }
        }
    }

    // Loading Spinner
    BusyIndicator {
        anchors.centerIn: parent
        running: isLoading
        visible: isLoading
        z: 50
    }

    // Launching/Installing Overlay
    Rectangle {
        id: progressOverlay
        anchors.fill: parent
        color: "black"
        opacity: 0.95
        visible: isLaunching || isInstalling
        z: 200

        ColumnLayout {
            anchors.centerIn: parent
            width: 800
            spacing: 30

            Text {
                text: isInstalling ? "Installing Game..." : "Launching Game..."
                color: "white"; font.pixelSize: 32; font.bold: true; Layout.alignment: Qt.AlignCenter
            }

            Text {
                text: isInstalling ? installStatus : launchStatus
                color: "#3a91f4"; font.pixelSize: 20; Layout.alignment: Qt.AlignCenter; Layout.fillWidth: true; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter
            }

            ProgressBar {
                Layout.fillWidth: true; height: 20
                value: isInstalling ? installProgress / 100.0 : (launchStatus.indexOf("running") !== -1 ? 1.0 : 0.5)
                background: Rectangle { color: "#333"; radius: 10 }
                contentItem: Item {
                    Rectangle { width: parent.parent.visualPosition * parent.width; height: parent.height; color: "#3a91f4"; radius: 10 }
                }
            }

            Rectangle {
                id: closeOverlayBtn
                width: 250; height: 60; radius: 30; color: activeFocus ? "#3d4450" : "#2a2a2a"
                border.color: activeFocus ? "white" : "transparent"; border.width: 3; Layout.alignment: Qt.AlignCenter
                Text { anchors.centerIn: parent; text: "DISMISS"; color: "white"; font.bold: true; font.pixelSize: 18 }
                MouseArea { anchors.fill: parent; onClicked: { isLaunching = false; isInstalling = false } }
                Keys.onPressed: (event) => { if (event.key === Qt.Key_Return || event.key === Qt.Key_Select) { isLaunching = false; isInstalling = false; event.accepted = true } }
                focus: progressOverlay.visible
            }
        }
    }

    // Uninstall Confirmation Dialog
    ConfirmDialog {
        id: uninstallConfirm
        title: "Uninstall Game?"
        message: "This will permanently remove the game files.\\nYour saves and cloud data will not be affected."
        confirmText: "CONFIRM"
        cancelText: "CANCEL"
        showStorageOptions: false
        onConfirmed: {
            gameManager.uninstall_game(appId)
            isLaunching = true
            launchStatus = "Uninstalling..."
        }
        onCancelled: {
            primaryActionBtn.forceActiveFocus()
        }
    }

    // Install Confirmation Dialog
    ConfirmDialog {
        id: installConfirm
        title: "Install Game?"
        message: "Choose installation location:"
        confirmText: "INSTALL"
        cancelText: "CANCEL"
        showStorageOptions: true
        onConfirmed: function(path) {
            gameManager.install_game(appId, path)
        }
        onCancelled: {
            primaryActionBtn.forceActiveFocus()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: !isLoading

        // Top Row: Poster
        Item {
            Layout.fillWidth: true; Layout.preferredHeight: 380
            Rectangle {
                anchors.left: parent.left; anchors.top: parent.top; anchors.leftMargin: 60; anchors.topMargin: 40
                width: 200; height: 300; radius: 4; clip: true; border.color: "#333"; border.width: 1
                Image { anchors.fill: parent; source: (gameData && gameData.artwork) ? gameData.artwork : ""; fillMode: Image.PreserveAspectCrop }
            }
        }

        // Action Bar
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 100; color: "#2b2e38"
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 60; anchors.rightMargin: 60; spacing: 0

                // Main Play/Install Button
                Rectangle {
                    id: primaryActionBtn
                    Layout.preferredWidth: 320; Layout.fillHeight: true
                    color: activeFocus ? "#28a745" : "#1a7531"
                    focus: true
                    RowLayout {
                        anchors.centerIn: parent; spacing: 15
                        Text { text: isDownloading ? "⬇" : "▶"; color: "white"; font.pixelSize: 24 }
                        Text {
                            text: isDownloading ? "DOWNLOADS" : (gameData && gameData.is_installed ? "Play" : "Install")
                            color: "white"; font.pixelSize: 28; font.bold: true
                        }
                    }
                    // Download progress bar under the button
                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width * (installProgress / 100.0)
                        height: 4
                        visible: isDownloading || isInstalling
                        color: "#3a91f4"
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (isDownloading) mainStack.push(downloadView)
                            else if (gameData.is_installed) gameManager.launch_game(appId)
                            else installConfirm.visible = true
                        }
                    }
                    Keys.onPressed: (event) => {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Select || event.key === Qt.Key_Enter) {
                            if (isDownloading) mainStack.push(downloadView)
                            else if (gameData.is_installed) gameManager.launch_game(appId)
                            else installConfirm.visible = true
                            event.accepted = true
                        }
                    }
                    KeyNavigation.right: statsBlock
                }

                // Stats Block
                Rectangle {
                    id: statsBlock; Layout.fillWidth: true; Layout.fillHeight: true; color: "#1e2129"
                    RowLayout {
                        anchors.fill: parent; anchors.leftMargin: 40; spacing: 40
                        ColumnLayout {
                            spacing: 2
                            visible: !detailRoot.isDownloading && !detailRoot.isInstalling
                            Text { text: "LAST PLAYED"; color: "#888"; font.pixelSize: 14; font.bold: true }
                            Text { 
                                text: detailRoot.lastPlayedText
                                color: "white"; font.pixelSize: 18; font.bold: true 
                            }
                        }
                        ColumnLayout {
                            spacing: 2
                            visible: !detailRoot.isDownloading && !detailRoot.isInstalling && detailRoot.gameSizeText !== ""
                            Text { text: "SIZE"; color: "#888"; font.pixelSize: 14; font.bold: true }
                            Text { 
                                text: detailRoot.gameSizeText
                                color: "white"; font.pixelSize: 18; font.bold: true 
                            }
                        }
                        ColumnLayout {
                            spacing: 2
                            visible: detailRoot.isDownloading || detailRoot.isInstalling
                            Text { text: "DOWNLOADING"; color: "#3a91f4"; font.pixelSize: 14; font.bold: true }
                            Text {
                                text: detailRoot.installStatus
                                color: "white"; font.pixelSize: 16; font.bold: true
                                Layout.fillWidth: true; elide: Text.ElideRight
                            }
                        }
                        ColumnLayout {
                            spacing: 2
                            visible: detailRoot.isDownloading || detailRoot.isInstalling
                            Text { text: "SPEED"; color: "#888"; font.pixelSize: 14; font.bold: true }
                            Text {
                                text: detailRoot.downloadSpeed
                                color: "white"; font.pixelSize: 18; font.bold: true
                            }
                        }
                        ColumnLayout {
                            spacing: 2
                            visible: detailRoot.isDownloading || detailRoot.isInstalling
                            Text { text: "ETA"; color: "#888"; font.pixelSize: 14; font.bold: true }
                            Text {
                                text: detailRoot.downloadEta !== "" ? detailRoot.downloadEta : "--:--:--"
                                color: "white"; font.pixelSize: 18; font.bold: true
                            }
                        }
                    }
                    KeyNavigation.left: primaryActionBtn
                    KeyNavigation.right: protonBadge
                }

                // Stylized Extra Buttons
                RowLayout {
                    Layout.fillHeight: true; spacing: 1
                    
                    // ProtonDB Badge/Button
                    Rectangle {
                        id: protonBadge
                        width: 140; Layout.fillHeight: true
                        color: activeFocus ? "#3d4450" : "#2b2e38"
                        visible: gameData && gameData.protondb && gameData.protondb.tier
                        
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 4
                            Rectangle {
                                Layout.preferredWidth: 100; Layout.preferredHeight: 30; radius: 4
                                color: {
                                    if (!gameData || !gameData.protondb) return "#444"
                                    var tier = gameData.protondb.tier
                                    if (tier === "platinum") return "#b4b4b4"
                                    if (tier === "gold") return "#cfb53b"
                                    if (tier === "silver") return "#c0c0c0"
                                    if (tier === "bronze") return "#cd7f32"
                                    return "#ff4444"
                                }
                                Text {
                                    anchors.centerIn: parent
                                    text: gameData && gameData.protondb ? gameData.protondb.tier.toUpperCase() : ""
                                    color: "black"; font.bold: true; font.pixelSize: 14
                                }
                            }
                            Text { text: "PROTONDB"; color: "white"; font.pixelSize: 10; font.bold: true; Layout.alignment: Qt.AlignCenter }
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if (gameData && gameData.protondb && gameData.protondb.steam_appid)
                                    Qt.openUrlExternally("https://www.protondb.com/app/" + gameData.protondb.steam_appid)
                            }
                        }
                        
                        Keys.onPressed: (event) => {
                            if ((event.key === Qt.Key_Return || event.key === Qt.Key_Select) && gameData.protondb.steam_appid) {
                                Qt.openUrlExternally("https://www.protondb.com/app/" + gameData.protondb.steam_appid)
                                event.accepted = true
                            }
                        }

                        KeyNavigation.left: statsBlock
                        KeyNavigation.right: steamBtn
                    }

                    Rectangle {
                        id: steamBtn
                        width: 100; Layout.fillHeight: true; color: activeFocus ? "#3d4450" : "#2b2e38"
                        Text { anchors.centerIn: parent; text: "ADD TO\nSTEAM"; font.pixelSize: 12; font.bold: true; color: "white"; horizontalAlignment: Text.AlignHCenter }
                        focus: true
                        KeyNavigation.left: protonBadge.visible ? protonBadge : statsBlock
                        KeyNavigation.right: uninstallBtn
                        MouseArea { anchors.fill: parent; onClicked: gameManager.inject_to_steam(appId) }
                        Keys.onPressed: (event) => { if (event.key === Qt.Key_Return || event.key === Qt.Key_Select) { gameManager.inject_to_steam(appId); event.accepted = true } }
                    }

                    Rectangle {
                        id: uninstallBtn
                        width: 100; Layout.fillHeight: true; color: activeFocus ? "#3d4450" : "#2b2e38"
                        visible: gameData && gameData.is_installed
                        Text { anchors.centerIn: parent; text: "UNINSTALL"; font.pixelSize: 12; font.bold: true; color: "white" }
                        KeyNavigation.left: steamBtn
                        MouseArea {
                            anchors.fill: parent
                            onClicked: { uninstallConfirm.visible = true }
                        }
                        Keys.onPressed: (event) => {
                            if (event.key === Qt.Key_Return || event.key === Qt.Key_Select) {
                                uninstallConfirm.visible = true; event.accepted = true
                            }
                        }
                    }
                }
            }
        }

        // Tab Strip
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 80; color: "transparent"
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 60; spacing: 40
                Row {
                    spacing: 15
                    Layout.alignment: Qt.AlignVCenter
                    Rectangle {
                        width: 140; height: 44; radius: 22; color: "#3d4450"
                        Text { anchors.centerIn: parent; text: "GAME INFO"; color: "white"; font.pixelSize: 16; font.bold: true }
                    }
                    Text { 
                        text: "✓"; color: "#28a745"; font.pixelSize: 24; font.bold: true
                        Layout.alignment: Qt.AlignVCenter
                        visible: gameData && gameData.protondb && (gameData.protondb.tier === "platinum" || gameData.protondb.tier === "gold")
                    }
                }
            }
        }

        // Main Content (Description)
        Flickable {
            id: contentFlick
            Layout.fillWidth: true; Layout.fillHeight: true
            Layout.leftMargin: 60; Layout.rightMargin: 60
            contentHeight: contentColumn.height; clip: true
            Column {
                id: contentColumn
                width: contentFlick.width
                spacing: 20
                Text {
                    width: parent.width; text: (gameData && gameData.app_title) ? gameData.app_title : ""
                    color: "white"; font.pixelSize: 36; font.bold: true; wrapMode: Text.WordWrap
                }
                Text {
                    width: parent.width; text: detailRoot.gameDescription
                    color: "#bbbbbb"; font.pixelSize: 19; wrapMode: Text.WordWrap; textFormat: Text.StyledText
                }
            }
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AlwaysOn }
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
                Layout.alignment: Qt.AlignVCenter
                controllerMode: gamepadManager.controllerConnected
                hints: [
                    {key: "D", label: "DOWNLOADS"},
                    {key: "Enter", controllerKey: "A", label: "SELECT"},
                    {key: "Esc", controllerKey: "B", label: "BACK"}
                ]
            }
        }
    }

    Connections {
        target: gameManager
        function onGame_info_ready(info) { 
            gameData = info
            isLoading = false
            primaryActionBtn.forceActiveFocus()
            
            if (info.metadata && info.metadata.description) {
                gameDescription = info.metadata.description
            }

            if (info.lastPlayed > 0) {
                lastPlayedText = new Date(info.lastPlayed * 1000).toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'})
            } else {
                lastPlayedText = "Never"
            }

            if (info.disk_size_gb) {
                gameSizeText = info.disk_size_gb + " GB"
            } else {
                gameSizeText = ""
            }
            
            checkDownloadStatus()
        }
        function onProton_info_ready(id, compat) {
            if (id === appId) {
                var newData = gameData
                newData.protondb = compat
                gameData = newData
                if (compat.steam_description) {
                    gameDescription = compat.steam_description
                }
            }
        }
        function onLast_played_updated(id, timestamp) {
            if (id === appId) {
                lastPlayedText = new Date(timestamp * 1000).toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'})
            }
        }
        function onLaunch_status_changed(status) { launchStatus = status; isLaunching = (status !== "Game finished.") }
        function onInstall_status_changed(id, progress, status) { if (id === appId) { installProgress = progress; installStatus = status; isInstalling = true } }
        function onInstall_finished(id, success) { if (id === appId) { isInstalling = false; if (!success) { installStatus = "Installation failed."; isInstalling = true } } }
        function onUninstall_status_changed(id, success) { if (id === appId) { isLaunching = false; if (!success) { launchStatus = "Uninstallation failed."; isLaunching = true } } }
    }

    function checkDownloadStatus() {
        if (!downloadManager) return;
        var found = false
        for (var i = 0; i < downloadManager.model.rowCount(); i++) {
            var index = downloadManager.model.index(i, 0)
            if (downloadManager.model.data(index, Qt.UserRole + 1) === appId) {
                var status = downloadManager.model.data(index, Qt.UserRole + 4)
                if (status === "Finished" || status === "Failed") {
                    found = false
                } else {
                    found = true
                    installProgress = downloadManager.model.data(index, Qt.UserRole + 3)
                    var speed = downloadManager.model.data(index, Qt.UserRole + 5)
                    var eta = downloadManager.model.data(index, Qt.UserRole + 6)
                    downloadSpeed = speed ? speed : ""
                    downloadEta = eta ? eta : ""
                    installStatus = status === "Downloading" ? installProgress.toFixed(1) + "%" : status
                }
                break
            }
        }
        if (!found && isDownloading) { 
            isDownloading = false
            isInstalling = false
            downloadSpeed = ""
            downloadEta = ""
            gameManager.fetch_game_info(appId) 
        } else if (found && !isDownloading) {
            isDownloading = true
        }
    }

    Connections {
        target: downloadManager ? downloadManager.model : null
        function onDataChanged() { checkDownloadStatus() }
        function onRowsInserted() { checkDownloadStatus() }
        function onRowsRemoved() { checkDownloadStatus() }
    }

    Component.onCompleted: {
        isLoading = false
        primaryActionBtn.forceActiveFocus()
        gameManager.fetch_game_info(appId)
    }
}
