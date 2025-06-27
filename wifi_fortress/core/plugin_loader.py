
import os
import importlib.util

class PluginLoader:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.plugins = {}

    def load_plugins(self, plugin_dir="wifi_fortress/plugins"):
        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                module_path = os.path.join(plugin_dir, filename)
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "Plugin"):
                    self.plugins[module_name] = module.Plugin(self.config_manager)

    def get_plugin(self, name):
        return self.plugins.get(name)

    def run_all(self):
        for plugin in self.plugins.values():
            plugin.run()
