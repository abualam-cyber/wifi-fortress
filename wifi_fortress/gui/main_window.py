
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from wifi_fortress.gui.dashboard import DashboardWindow

def launch_gui(config_manager, plugin_loader):
    app = QApplication([])
    main_window = MainWindow(config_manager, plugin_loader)
    main_window.show()
    app.exec_()

class MainWindow(QMainWindow):
    def __init__(self, config_manager, plugin_loader):
        super().__init__()
        self.setWindowTitle("WiFi Fortress")
        self.setGeometry(100, 100, 600, 400)
        self.config_manager = config_manager
        self.plugin_loader = plugin_loader

        layout = QVBoxLayout()
        label = QLabel("Welcome to WiFi Fortress\nSecure your wireless networks.")
        btn_dashboard = QPushButton("Launch Dashboard")
        btn_dashboard.clicked.connect(self.launch_dashboard)

        layout.addWidget(label)
        layout.addWidget(btn_dashboard)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def launch_dashboard(self):
        self.dashboard = DashboardWindow(self.config_manager, self.plugin_loader)
        self.dashboard.show()
