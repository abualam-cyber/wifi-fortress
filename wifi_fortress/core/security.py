
import subprocess
import platform
import logging

class Security:
    def __init__(self):
        self.logger = logging.getLogger("Security")

    def run_command(self, command):
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            return output.decode()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {e.output.decode()}")
            return ""

    def check_open_ports(self):
        if platform.system() == "Linux":
            return self.run_command("ss -tuln")
        else:
            return self.run_command("netstat -an")

    def check_running_services(self):
        return self.run_command("systemctl list-units --type=service --state=running")

    def scan_for_rogue_devices(self):
        return self.run_command("arp-scan --localnet")
