
import unittest
from wifi_fortress.core.plugin_loader import PluginLoader
from wifi_fortress.core.config_manager import ConfigManager

class TestPluginLoader(unittest.TestCase):
    def test_plugin_loading(self):
        config = ConfigManager("test_config.json")
        loader = PluginLoader(config)
        loader.load_plugins("wifi_fortress/plugins")
        self.assertGreater(len(loader.plugins), 0)
