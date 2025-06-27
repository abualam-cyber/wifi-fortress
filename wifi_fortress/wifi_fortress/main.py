import sys
import os
from PyQt5.QtWidgets import QApplication
from wifi_fortress.gui.main_window import MainWindow
from wifi_fortress.core.plugin_loader import PluginLoader

def main():
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Initialize plugin system
    plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
    plugin_loader = PluginLoader(plugin_dir)
    
    # Create and show main window
    window = MainWindow(plugin_loader)
    window.show()
    
    # Start event loop
    exit_code = app.exec_()
    
    # Cleanup
    for plugin_name in plugin_loader.get_active_plugins():
        plugin_loader.deactivate_plugin(plugin_name)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()