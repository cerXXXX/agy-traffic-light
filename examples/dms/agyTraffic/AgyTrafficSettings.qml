import QtQuick
import qs.Common
import qs.Widgets
import qs.Modules.Plugins

PluginSettings {
    pluginId: "agyTraffic"

    StyledText {
        width: parent.width
        text: "Antigravity Traffic Light Settings"
        font.pixelSize: Theme.fontSizeLarge
        font.weight: Font.Bold
        color: Theme.surfaceText
    }

    ToggleSetting {
        settingKey: "showBackground"
        label: "Show Widget Background"
        description: "Show background pill behind the traffic light circle"
        defaultValue: false
    }

    StringSetting {
        settingKey: "daemonUrl"
        label: "Daemon URL"
        description: "Status daemon endpoint"
        placeholder: "http://127.0.0.1:9876"
        defaultValue: "http://127.0.0.1:9876"
    }
}
