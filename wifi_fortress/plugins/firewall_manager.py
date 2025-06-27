import subprocess

class Plugin:
    def __init__(self, config_manager):
        self.name = "Firewall Manager"
        self.config = config_manager

    def run(self):
        print(f"[{self.name}] Checking firewall rules (ufw):")
        try:
            result = subprocess.check_output(["sudo", "ufw", "status"], stderr=subprocess.DEVNULL)
            print(result.decode())
        except Exception as e:
            print(f"Error: {str(e)}")
