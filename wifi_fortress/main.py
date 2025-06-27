
import sys
from wifi_fortress.core.plugin_loader import PluginLoader
from wifi_fortress.core.config_manager import ConfigManager
from wifi_fortress.core.logging_manager import setup_logging
from wifi_fortress.gui.main_window import launch_gui

def main():
    setup_logging()
    config = ConfigManager()
    plugin_loader = PluginLoader(config)
    plugin_loader.load_plugins()

    launch_gui(config, plugin_loader)

if __name__ == "__main__":
    main()
