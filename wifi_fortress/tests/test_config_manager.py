
import unittest
from wifi_fortress.core.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.config = ConfigManager("test_config.json")

    def test_default_config(self):
        self.assertEqual(self.config.get("scan_interval"), 10)

    def test_set_and_get_config(self):
        self.config.set("test_key", "value")
        self.assertEqual(self.config.get("test_key"), "value")
