from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QStatusBar, QMessageBox, QTabWidget)
from PyQt5.QtCore import Qt
from ..core.plugin_loader import PluginLoader
from .dashboard import DashboardWidget

class MainWindow(QMainWindow):
    def __init__(self, plugin_loader: PluginLoader):
        super().__init__()
        self.plugin_loader = plugin_loader
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('WiFi Fortress')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create header
        header = QLabel('WiFi Fortress - Network Security Suite')
        header.setStyleSheet('font-size: 18px; font-weight: bold; margin: 10px;')
        layout.addWidget(header)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Add dashboard tab
        self.dashboard = DashboardWidget()
        tabs.addTab(self.dashboard, 'Dashboard')
        
        # Add plugins tab
        plugins_widget = QWidget()
        plugins_layout = QVBoxLayout(plugins_widget)
        
        # Create plugin table
        self.plugin_table = QTableWidget()
        self.plugin_table.setColumnCount(5)
        self.plugin_table.setHorizontalHeaderLabels(['Name', 'Description', 'Version', 'Author', 'Status'])
        self.plugin_table.horizontalHeader().setStretchLastSection(True)
        plugins_layout.addWidget(self.plugin_table)
        
        # Create button row
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton('Refresh Plugins')
        self.refresh_btn.clicked.connect(self.refresh_plugins)
        button_layout.addWidget(self.refresh_btn)
        
        self.start_btn = QPushButton('Start Selected')
        self.start_btn.clicked.connect(self.start_selected_plugin)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton('Stop Selected')
        self.stop_btn.clicked.connect(self.stop_selected_plugin)
        button_layout.addWidget(self.stop_btn)
        
        plugins_layout.addLayout(button_layout)
        
        # Add plugins tab
        tabs.addTab(plugins_widget, 'Plugins')
        
        # Add tabs to main layout
        layout.addWidget(tabs)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Load plugins initially
        self.refresh_plugins()
        
    def refresh_plugins(self):
        """Refresh the plugin list"""
        self.plugin_table.setRowCount(0)
        available_plugins = self.plugin_loader.get_available_plugins()
        active_plugins = self.plugin_loader.get_active_plugins()
        
        self.plugin_table.setRowCount(len(available_plugins))
        for row, name in enumerate(available_plugins):
            plugin_class = self.plugin_loader.plugins[name]
            
            self.plugin_table.setItem(row, 0, QTableWidgetItem(plugin_class.name))
            self.plugin_table.setItem(row, 1, QTableWidgetItem(plugin_class.description))
            self.plugin_table.setItem(row, 2, QTableWidgetItem(plugin_class.version))
            self.plugin_table.setItem(row, 3, QTableWidgetItem(plugin_class.author))
            
            status = 'Active' if name in active_plugins else 'Inactive'
            self.plugin_table.setItem(row, 4, QTableWidgetItem(status))
        
        self.status_bar.showMessage(f'Loaded {len(available_plugins)} plugins')
        
    def get_selected_plugin(self):
        """Get the currently selected plugin name"""
        selected_rows = self.plugin_table.selectedItems()
        if not selected_rows:
            return None
        return self.plugin_table.item(selected_rows[0].row(), 0).text()
        
    def start_selected_plugin(self):
        """Start the selected plugin"""
        plugin_name = self.get_selected_plugin()
        if not plugin_name:
            QMessageBox.warning(self, 'Error', 'Please select a plugin first')
            return
            
        try:
            self.plugin_loader.activate_plugin(plugin_name)
            self.refresh_plugins()
            self.status_bar.showMessage(f'Started plugin: {plugin_name}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to start plugin: {str(e)}')
            
    def stop_selected_plugin(self):
        """Stop the selected plugin"""
        plugin_name = self.get_selected_plugin()
        if not plugin_name:
            QMessageBox.warning(self, 'Error', 'Please select a plugin first')
            return
            
        try:
            self.plugin_loader.deactivate_plugin(plugin_name)
            self.refresh_plugins()
            self.status_bar.showMessage(f'Stopped plugin: {plugin_name}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to stop plugin: {str(e)}')
