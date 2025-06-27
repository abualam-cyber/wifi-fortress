
import subprocess
import logging

class Sandbox:
    def __init__(self):
        self.logger = logging.getLogger("Sandbox")

    def safe_exec(self, cmd):
        if not isinstance(cmd, str):
            self.logger.error("Invalid command type.")
            return ""
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=15)
            return output.decode()
        except Exception as e:
            self.logger.error(f"Execution failed: {str(e)}")
            return ""
