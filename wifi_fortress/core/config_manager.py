
import json
import os

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.settings = {}
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = {"scan_interval": 10, "plugins": []}
            self.save_config()

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_config()
