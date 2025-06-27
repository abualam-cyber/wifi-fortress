
import os
import json
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_json_report(self, data, filename_prefix="report"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        path = os.path.join(self.output_dir, filename)
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"[+] JSON Report saved: {path}")
        return path

    def generate_summary(self, plugin_loader):
        results = {}
        for name, plugin in plugin_loader.plugins.items():
            try:
                output = plugin.run()
                results[name] = output or "Completed successfully."
            except Exception as e:
                results[name] = f"Error: {str(e)}"
        return results
