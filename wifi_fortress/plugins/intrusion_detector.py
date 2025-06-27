
import subprocess

class Plugin:
    def __init__(self, config_manager):
        self.name = "Intrusion Detector"
        self.config = config_manager

    def run(self):
        try:
            result = subprocess.check_output(["sudo", "logwatch", "--range", "today"], stderr=subprocess.DEVNULL)
            print(f"[{self.name}]\n{result.decode()}")
        except Exception as e:
            print(f"[{self.name}] Error: {str(e)}")
