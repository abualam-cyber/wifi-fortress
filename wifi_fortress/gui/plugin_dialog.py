
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class PluginDialog(QDialog):
    def __init__(self, plugin_name, plugin_instance):
        super().__init__()
        self.setWindowTitle(f"Manage Plugin: {plugin_name}")
        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Plugin: {plugin_name}"))
        run_button = QPushButton("Run Plugin")
        run_button.clicked.connect(lambda: plugin_instance.run())
        layout.addWidget(run_button)

        self.setLayout(layout)
