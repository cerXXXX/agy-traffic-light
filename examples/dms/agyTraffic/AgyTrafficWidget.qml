import QtQuick
import Quickshell
import qs.Common
import qs.Services
import qs.Widgets
import qs.Modules.Plugins

PluginComponent {
    id: root

    property string agentState: "offline"
    property string statusText: "Offline"
    property var sessions: []

    Timer {
        interval: 350
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "http://127.0.0.1:9876/status");
            xhr.onreadystatechange = function() {
                if (xhr.readyState === XMLHttpRequest.DONE) {
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            root.agentState = data.state || "offline";
                            root.sessions = data.sessions || [];
                            if (root.agentState === "ask") root.statusText = "Attention Required";
                            else if (root.agentState === "running") root.statusText = "Agent Working";
                            else if (root.agentState === "idle") root.statusText = "Agent Idle";
                            else root.statusText = "Offline";
                        } catch (e) {}
                    } else {
                        root.agentState = "offline";
                        root.statusText = "Daemon Offline";
                        root.sessions = [];
                    }
                }
            };
            xhr.send();
        }
    }

    readonly property color stateColor: {
        if (root.agentState === "ask") return "#ff1744";     // 🔴 Neon Red
        if (root.agentState === "running") return "#ffdd00"; // 🟡 Neon Yellow
        if (root.agentState === "idle") return "#00ff88";    // 🟢 Neon Green
        return "#6c7086";                                    // ⚪ Offline
    }

    horizontalBarPill: Component {
        StyledRect {
            width: pillRow.implicitWidth + Theme.spacingM * 1.5
            height: parent.widgetThickness
            radius: Theme.cornerRadius
            color: root.agentState === "ask" ? "#33ff1744" : Theme.surfaceContainerHigh
            border.color: root.agentState === "ask" ? "#ff1744" : "transparent"
            border.width: root.agentState === "ask" ? 1 : 0

            Row {
                id: pillRow
                anchors.centerIn: parent
                spacing: Theme.spacingS

                // Colored glowing circle
                Rectangle {
                    width: 14
                    height: 14
                    radius: 7
                    color: root.stateColor
                    anchors.verticalCenter: parent.verticalCenter
                    border.color: Theme.surfaceContainerHighest
                    border.width: 1.5

                    // Outer pulse ring when running or requiring approval
                    Rectangle {
                        anchors.centerIn: parent
                        width: 20
                        height: 20
                        radius: 10
                        color: "transparent"
                        border.color: root.stateColor
                        border.width: 1.5
                        opacity: (root.agentState === "running" || root.agentState === "ask") ? 0.7 : 0.0
                        visible: opacity > 0
                    }
                }

                // Subtitle if running
                StyledText {
                    visible: root.agentState === "running" || root.agentState === "ask"
                    text: root.agentState === "ask" ? "Confirm" : "Agent"
                    font.pixelSize: Theme.fontSizeSmall
                    font.weight: Font.Bold
                    color: root.stateColor
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }

    verticalBarPill: Component {
        StyledRect {
            width: parent.widgetThickness
            height: 32
            radius: Theme.cornerRadius
            color: Theme.surfaceContainerHigh

            Rectangle {
                width: 14
                height: 14
                radius: 7
                color: root.stateColor
                anchors.centerIn: parent
            }
        }
    }

    popoutContent: Component {
        PopoutComponent {
            id: popout
            headerText: "Antigravity Agent"
            detailsText: root.statusText
            showCloseButton: true

            Column {
                width: parent.width
                spacing: Theme.spacingM

                StyledRect {
                    width: parent.width
                    height: sessionListCol.implicitHeight + Theme.spacingM * 2
                    radius: Theme.cornerRadius
                    color: Theme.surfaceContainerHigh

                    Column {
                        id: sessionListCol
                        anchors.fill: parent
                        anchors.margins: Theme.spacingM
                        spacing: Theme.spacingS

                        StyledText {
                            text: root.sessions.length > 0 ? "Active Sessions (" + root.sessions.length + "):" : "No active sessions running"
                            font.pixelSize: Theme.fontSizeMedium
                            font.weight: Font.Bold
                            color: Theme.surfaceText
                        }

                        Repeater {
                            model: root.sessions
                            StyledText {
                                text: "• [" + modelData.workspace + (modelData.host !== "localhost" ? "@" + modelData.host : "") + "]: " + modelData.substatus
                                font.pixelSize: Theme.fontSizeSmall
                                color: Theme.surfaceTextMedium
                                wrapMode: Text.Wrap
                                width: sessionListCol.width
                            }
                        }
                    }
                }

                Row {
                    spacing: Theme.spacingM
                    anchors.horizontalCenter: parent.horizontalCenter

                    DankButton {
                        text: "Clear Finished Sessions"
                        onClicked: {
                            var xhr = new XMLHttpRequest();
                            xhr.open("POST", "http://127.0.0.1:9876/clear");
                            xhr.send();
                        }
                    }
                }
            }
        }
    }

    popoutWidth: 380
    popoutHeight: 260
}
