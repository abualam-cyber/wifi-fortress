import subprocess
import psutil

class Plugin:
    def __init__(self, config_manager):
        self.name = "Network Monitor"
        self.config = config_manager

    def run(self):
        print(f"[{self.name}] Active network connections:")
        connections = psutil.net_connections(kind='inet')
        for conn in connections[:10]:  # Show first 10
            print(conn)
