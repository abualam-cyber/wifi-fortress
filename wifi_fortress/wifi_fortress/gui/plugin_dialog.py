from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QListWidget,
                             QListWidgetItem, QMessageBox, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, Type
from wifi_fortress.core.plugin_loader import Plugin, PluginLoader

class PluginListItem(QWidget):
    """Custom widget for plugin list items"""
    
    def __init__(self, plugin: Plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Plugin info
        info_layout = QVBoxLayout()
        name_label = QLabel(f'<b>{plugin.name}</b> v{plugin.version}')
        desc_label = QLabel(plugin.description)
        desc_label.setWordWrap(True)
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Status and controls
        status_layout = QVBoxLayout()
        self.status_label = QLabel('Enabled' if plugin.enabled else 'Disabled')
        self.toggle_button = QPushButton('Disable' if plugin.enabled else 'Enable')
        self.toggle_button.clicked.connect(self._toggle_plugin)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.toggle_button)
        
        layout.addLayout(status_layout)
        self.setLayout(layout)
        
    def _toggle_plugin(self):
        """Toggle plugin enabled state"""
        try:
            if self.plugin.enabled:
                if self.plugin.cleanup():
                    self.plugin.enabled = False
                    self.status_label.setText('Disabled')
                    self.toggle_button.setText('Enable')
            else:
                if self.plugin.initialize():
                    self.plugin.enabled = True
                    self.status_label.setText('Enabled')
                    self.toggle_button.setText('Disable')
        except Exception as e:
            QMessageBox.warning(
                self,
                'Plugin Error',
                f'Error toggling plugin {self.plugin.name}: {str(e)}'
            )

class PluginDialog(QDialog):
    """Dialog for managing plugins"""
    
    plugin_state_changed = pyqtSignal(str, bool)  # plugin_name, enabled
    
    def __init__(self, plugin_loader: PluginLoader, parent=None):
        super().__init__(parent)
        self.plugin_loader = plugin_loader
        self.setWindowTitle('Manage Plugins')
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Plugin list
        self.plugin_list = QListWidget()
        self.plugin_list.setSpacing(2)
        layout.addWidget(QLabel('<b>Installed Plugins</b>'))
        layout.addWidget(self.plugin_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton('Refresh')
        refresh_btn.clicked.connect(self.refresh_plugins)
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.refresh_plugins()
        
    def refresh_plugins(self):
        """Refresh the plugin list"""
        self.plugin_list.clear()
        
        try:
            # Discover plugins
            plugin_paths = self.plugin_loader.discover_plugins()
            
            for path in plugin_paths:
                try:
                    # Load plugin if not already loaded
                    if not self.plugin_loader.load_plugin(path):
                        continue
                        
                    # Get plugin instance
                    plugin_name = path.split('/')[-1].replace('.py', '')
                    plugin = self.plugin_loader.instantiate_plugin(plugin_name)
                    
                    # Create list item
                    item = QListWidgetItem()
                    item.setSizeHint(QSize(0, 80))  # Fixed height for consistency
                    
                    widget = PluginListItem(plugin)
                    self.plugin_list.addItem(item)
                    self.plugin_list.setItemWidget(item, widget)
                    
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        'Plugin Error',
                        f'Error loading plugin from {path}: {str(e)}'
                    )
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                'Plugin System Error',
                f'Error refreshing plugins: {str(e)}'
            )
            
    def showEvent(self, event):
        """Refresh plugins when dialog is shown"""
        super().showEvent(event)
        self.refresh_plugins()
