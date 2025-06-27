
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit

class DashboardWindow(QWidget):
    def __init__(self, config_manager, plugin_loader):
        super().__init__()
        self.setWindowTitle("WiFi Fortress Dashboard")
        self.setGeometry(150, 150, 700, 500)
        self.config = config_manager
        self.plugin_loader = plugin_loader

        layout = QVBoxLayout()
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        run_all_btn = QPushButton("Run All Plugins")
        run_all_btn.clicked.connect(self.run_all_plugins)

        layout.addWidget(QLabel("Plugin Output:"))
        layout.addWidget(run_all_btn)
        layout.addWidget(self.output)
        self.setLayout(layout)

    def run_all_plugins(self):
        self.output.clear()
        for name, plugin in self.plugin_loader.plugins.items():
            self.output.append(f"[Running {name}]")
            try:
                plugin.run()
                self.output.append(f"[{name}] ✅ Completed\n")
            except Exception as e:
                self.output.append(f"[{name}] ❌ Failed: {str(e)}\n")
