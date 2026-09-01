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

    readonly property bool showBackground: pluginData.showBackground || false
    readonly property string daemonUrl: pluginData.daemonUrl || "http://127.0.0.1:9876"
    readonly property bool hasFinishedSessions: root.sessions.some(function(s) { return s.state === "idle"; })

    onBarConfigChanged: updateCustomBarConfig()
    onShowBackgroundChanged: updateCustomBarConfig()
    Component.onCompleted: updateCustomBarConfig()

    function updateCustomBarConfig() {
        if (!barConfig) {
            barConfig = { noBackground: !root.showBackground, _customized: true };
            return;
        }
        if (barConfig._customized && barConfig.noBackground === !root.showBackground)
            return;

        var cfg = {};
        for (var k in barConfig) cfg[k] = barConfig[k];
        cfg.noBackground = !root.showBackground;
        cfg._customized = true;
        barConfig = cfg;
    }

    Timer {
        interval: 350
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            var xhr = new XMLHttpRequest();
            var endpoint = (root.daemonUrl ? root.daemonUrl.replace(/\/+$/, "") : "http://127.0.0.1:9876") + "/status";
            xhr.open("GET", endpoint);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === XMLHttpRequest.DONE) {
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            root.agentState = data.state || "offline";
                            root.sessions = data.sessions || [];
                            if (root.agentState === "ask") root.statusText = "Attention Required";
                            else if (root.agentState === "running") root.statusText = "Agent Working";
                            else if (root.agentState === "idle") root.statusText = "Ready for Input";
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

    // Horizontal bar pill: dynamic scaling with enlarged inner core
    horizontalBarPill: Component {
        Item {
            id: pillContent

            readonly property real thickness: (root.widgetThickness > 0) ? root.widgetThickness : 30
            readonly property real horizontalPadding: (root.barConfig && root.barConfig.removeWidgetPadding) ? 0 : Theme.snap((root.barConfig && root.barConfig.widgetPadding !== undefined ? root.barConfig.widgetPadding : 12) * (thickness / 30), 1)
            // Even integer dimensions for sharp, centered rendering (86.7% of bar height -> 26px on 30px bar)
            readonly property int outerSize: Math.max(12, (Math.floor(thickness * 0.867) & ~1))
            readonly property int innerSize: Math.max(8, (Math.floor(outerSize * 0.693) & ~1))

            implicitWidth: Math.max(0, pillContent.outerSize - horizontalPadding * 2)
            implicitHeight: thickness
            width: pillContent.outerSize
            height: thickness

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
                    opacity: root.agentState === "offline" ? 0.30 : 0.80

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

                // Enlarged Inner Core Dot (centered inside outerHalo)
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

            readonly property real thickness: (root.widgetThickness > 0) ? root.widgetThickness : 30
            readonly property real horizontalPadding: (root.barConfig && root.barConfig.removeWidgetPadding) ? 0 : Theme.snap((root.barConfig && root.barConfig.widgetPadding !== undefined ? root.barConfig.widgetPadding : 12) * (thickness / 30), 1)
            readonly property int outerSize: Math.max(12, (Math.floor(thickness * 0.867) & ~1))
            readonly property int innerSize: Math.max(8, (Math.floor(outerSize * 0.693) & ~1))

            implicitWidth: thickness
            implicitHeight: Math.max(0, vPillContent.outerSize - horizontalPadding * 2)
            width: thickness
            height: vPillContent.outerSize

            Item {
                anchors.centerIn: parent
                width: vPillContent.outerSize
                height: vPillContent.outerSize

                // Outer Halo Ring
                Rectangle {
                    id: vOuterHalo
                    anchors.fill: parent
                    radius: width / 2
                    color: "transparent"
                    border.color: root.stateColor
                    border.width: 1.5
                    opacity: root.agentState === "offline" ? 0.30 : 0.80

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

                // Enlarged Inner Core Dot
                Rectangle {
                    id: vInnerCore
                    anchors.centerIn: parent
                    width: vPillContent.innerSize
                    height: vPillContent.innerSize
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

    // Popout on click
    popoutContent: Component {
        PopoutComponent {
            id: popout
            showCloseButton: false

            Column {
                width: parent.width
                spacing: Theme.spacingS

                // Clean Header
                Item {
                    width: parent.width
                    height: 24

                    StyledText {
                        anchors.left: parent.left
                        anchors.leftMargin: Theme.spacingXS
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Antigravity Agent"
                        font.pixelSize: Theme.fontSizeLarge
                        font.weight: Font.Bold
                        color: Theme.surfaceText
                    }

                    Rectangle {
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        width: 24
                        height: 24
                        radius: 12
                        color: closeArea.containsMouse ? Theme.errorHover : Theme.withAlpha(Theme.errorHover, 0)

                        DankIcon {
                            anchors.centerIn: parent
                            name: "close"
                            size: Theme.iconSize - 6
                            color: closeArea.containsMouse ? Theme.error : Theme.surfaceText
                        }

                        MouseArea {
                            id: closeArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onPressed: {
                                if (popout.closePopout) popout.closePopout();
                            }
                        }
                    }
                }

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
                            font.pixelSize: Theme.fontSizeSmall
                            font.weight: Font.DemiBold
                            color: Theme.surfaceVariantText
                        }

                        Repeater {
                            model: root.sessions
                            StyledText {
                                text: "• [" + modelData.workspace + (modelData.host !== "localhost" ? "@" + modelData.host : "") + "]: " + modelData.substatus
                                font.pixelSize: Theme.fontSizeSmall
                                color: Theme.surfaceText
                                wrapMode: Text.Wrap
                                width: sessionListCol.width
                            }
                        }
                    }
                }
            }
        }
    }

    popoutWidth: 380
    popoutHeight: 130
}
