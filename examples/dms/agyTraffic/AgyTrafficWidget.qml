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
        if (root.agentState === "running") return "#ffdd00"; // 🟡 Neon Amber/Yellow
        if (root.agentState === "idle") return "#00ff88";    // 🟢 Neon Green
        return "#6c7086";                                    // ⚪ Offline
    }

    // Horizontal bar pill: dynamically sized based on widgetThickness and mathematically centered
    horizontalBarPill: Component {
        Item {
            id: pillContent

            readonly property real thickness: (parent && parent.widgetThickness > 0) ? parent.widgetThickness : 30
            // Even integer dimensions to avoid subpixel shifting
            readonly property int outerSize: (Math.floor(thickness * 0.80) & ~1)
            readonly property int innerSize: (Math.floor(outerSize * 0.58) & ~1)

            implicitWidth: 0
            implicitHeight: thickness

            Item {
                anchors.centerIn: parent
                width: pillContent.outerSize
                height: pillContent.outerSize

                // Outer Halo Ring
                Rectangle {
                    id: outerHalo
                    anchors.fill: parent
                    radius: width / 2
                    color: "transparent"
                    border.color: root.stateColor
                    border.width: 1.5
                    opacity: root.agentState === "offline" ? 0.25 : 0.75

                    Behavior on border.color {
                        ColorAnimation { duration: 250 }
                    }

                    SequentialAnimation on opacity {
                        running: root.agentState === "running" || root.agentState === "ask"
                        loops: Animation.Infinite
                        NumberAnimation { from: 0.35; to: 0.95; duration: root.agentState === "ask" ? 500 : 1000; easing.type: Easing.InOutQuad }
                        NumberAnimation { from: 0.95; to: 0.35; duration: root.agentState === "ask" ? 500 : 1000; easing.type: Easing.InOutQuad }
                    }
                }

                // Inner Core Dot (centered inside outerHalo)
                Rectangle {
                    id: innerCore
                    anchors.centerIn: parent
                    width: pillContent.innerSize
                    height: pillContent.innerSize
                    radius: width / 2
                    color: root.stateColor
                    border.color: Theme.surfaceContainerHighest
                    border.width: 1.5

                    Behavior on color {
                        ColorAnimation { duration: 250 }
                    }
                }
            }
        }
    }

    // Vertical bar pill
    verticalBarPill: Component {
        Item {
            id: vPillContent

            readonly property real thickness: (parent && parent.widgetThickness > 0) ? parent.widgetThickness : 30
            readonly property int outerSize: (Math.floor(thickness * 0.80) & ~1)
            readonly property int innerSize: (Math.floor(outerSize * 0.58) & ~1)

            implicitWidth: thickness
            implicitHeight: 0

            Item {
                anchors.centerIn: parent
                width: vPillContent.outerSize
                height: vPillContent.outerSize

                Rectangle {
                    anchors.fill: parent
                    radius: width / 2
                    color: "transparent"
                    border.color: root.stateColor
                    border.width: 1.5
                    opacity: 0.75
                }

                Rectangle {
                    anchors.centerIn: parent
                    width: vPillContent.innerSize
                    height: vPillContent.innerSize
                    radius: width / 2
                    color: root.stateColor
                    border.color: Theme.surfaceContainerHighest
                    border.width: 1.5
                }
            }
        }
    }

    // Popout on click
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
