import sys
from typing import Dict, List, Optional
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem,
                           QHeaderView, QPushButton, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette

from ..core.health_monitor import HealthMonitor, HealthStatus
from ..core.network_mapper import NetworkMapper
from ..core.plugin_loader import PluginLoader
from ..core.logging_manager import LoggingManager

class DashboardWidget(QWidget):
    """Main dashboard widget for WiFi Fortress"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize components
        self.health_monitor = HealthMonitor()
        self.network_mapper = NetworkMapper()
        self.plugin_loader = PluginLoader()
        self.logging_manager = LoggingManager()
        
        # Setup UI
        self.setup_ui()
        
        # Start monitoring
        self.health_monitor.start_monitoring(interval=30)  # 30 second updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(1000)  # 1 second refresh
        
    def setup_ui(self):
        """Setup dashboard UI"""
        layout = QVBoxLayout()
        
        # Status overview
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        status_layout = QHBoxLayout()
        
        # System health
        self.health_status = StatusWidget("System Health")
        status_layout.addWidget(self.health_status)
        
        # Network status
        self.network_status = StatusWidget("Network Status")
        status_layout.addWidget(self.network_status)
        
        # Security status
        self.security_status = StatusWidget("Security Status")
        status_layout.addWidget(self.security_status)
        
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)
        
        # Detail tabs
        tabs = QTabWidget()
        
        # System metrics tab
        self.metrics_widget = MetricsWidget()
        tabs.addTab(self.metrics_widget, "System Metrics")
        
        # Network devices tab
        self.devices_widget = NetworkDevicesWidget()
        tabs.addTab(self.devices_widget, "Network Devices")
        
        # Security alerts tab
        self.alerts_widget = SecurityAlertsWidget()
        tabs.addTab(self.alerts_widget, "Security Alerts")
        
        # Active plugins tab
        self.plugins_widget = PluginsWidget(self.plugin_loader)
        tabs.addTab(self.plugins_widget, "Plugins")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
        
    def update_dashboard(self):
        """Update all dashboard components"""
        try:
            # Update system health
            health_status = self.health_monitor.get_current_status()
            self.health_status.update_status(
                health_status,
                self.health_monitor.collect_metrics()
            )
            
            # Update network status
            self.network_status.update_status(
                "OK" if self.network_mapper.get_active_devices() else "WARNING",
                {"active_devices": len(self.network_mapper.get_active_devices())}
            )
            
            # Update security status
            alerts = self.alerts_widget.get_active_alerts()
            security_status = "CRITICAL" if any(a["level"] == "HIGH" for a in alerts) else \
                            "WARNING" if alerts else "OK"
            self.security_status.update_status(
                security_status,
                {"active_alerts": len(alerts)}
            )
            
            # Update detail widgets
            self.metrics_widget.update_metrics(self.health_monitor.collect_metrics())
            self.devices_widget.update_devices(self.network_mapper.get_active_devices())
            self.plugins_widget.update_plugins()
            
        except Exception as e:
            self.logging_manager.get_logger("dashboard").error(
                f"Error updating dashboard: {str(e)}"
            )
            
    def closeEvent(self, event):
        """Handle dashboard closure"""
        self.update_timer.stop()
        self.health_monitor.stop_monitoring()
        super().closeEvent(event)

class StatusWidget(QFrame):
    """Widget for displaying component status"""
    
    def __init__(self, title: str):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Status
        self.status_label = QLabel("OK")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Details
        self.details_label = QLabel()
        self.details_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.details_label)
        
        self.setLayout(layout)
        
    def update_status(self, status: str, details: Dict = None):
        """Update status display
        
        Args:
            status: Status string (OK, WARNING, CRITICAL)
            details: Optional status details
        """
        self.status_label.setText(status)
        
        # Set color based on status
        color = {
            "OK": QColor(0, 255, 0),      # Green
            "WARNING": QColor(255, 165, 0),  # Orange
            "CRITICAL": QColor(255, 0, 0)    # Red
        }.get(status, QColor(128, 128, 128))  # Gray default
        
        palette = self.status_label.palette()
        palette.setColor(QPalette.WindowText, color)
        self.status_label.setPalette(palette)
        
        # Update details
        if details:
            details_text = "\n".join(f"{k}: {v}" for k, v in details.items())
            self.details_label.setText(details_text)

class MetricsWidget(QWidget):
    """Widget for displaying system metrics"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # CPU usage
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU Usage:"))
        self.cpu_bar = QProgressBar()
        cpu_layout.addWidget(self.cpu_bar)
        layout.addLayout(cpu_layout)
        
        # Memory usage
        mem_layout = QHBoxLayout()
        mem_layout.addWidget(QLabel("Memory Usage:"))
        self.mem_bar = QProgressBar()
        mem_layout.addWidget(self.mem_bar)
        layout.addLayout(mem_layout)
        
        # Network I/O
        self.net_table = QTableWidget()
        self.net_table.setColumnCount(3)
        self.net_table.setHorizontalHeaderLabels(["Interface", "Sent", "Received"])
        header = self.net_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.net_table)
        
        self.setLayout(layout)
        
    def update_metrics(self, metrics):
        """Update displayed metrics"""
        # Update CPU and memory bars
        self.cpu_bar.setValue(int(metrics.cpu_percent))
        self.mem_bar.setValue(int(metrics.memory_percent))
        
        # Update network table
        self.net_table.setRowCount(len(metrics.network_io))
        for row, (interface, io) in enumerate(metrics.network_io.items()):
            self.net_table.setItem(row, 0, QTableWidgetItem(interface))
            self.net_table.setItem(
                row, 1,
                QTableWidgetItem(f"{io['bytes_sent'] / 1024 / 1024:.1f} MB")
            )
            self.net_table.setItem(
                row, 2,
                QTableWidgetItem(f"{io['bytes_recv'] / 1024 / 1024:.1f} MB")
            )

class NetworkDevicesWidget(QWidget):
    """Widget for displaying network devices"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # Devices table
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(4)
        self.devices_table.setHorizontalHeaderLabels([
            "IP Address", "MAC Address", "Hostname", "Last Seen"
        ])
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.devices_table)
        
        # Scan button
        scan_button = QPushButton("Scan Network")
        scan_button.clicked.connect(self.scan_network)
        layout.addWidget(scan_button)
        
        self.setLayout(layout)
        
    def update_devices(self, devices: List):
        """Update device list"""
        self.devices_table.setRowCount(len(devices))
        for row, device in enumerate(devices):
            self.devices_table.setItem(row, 0, QTableWidgetItem(device.ip_address))
            self.devices_table.setItem(row, 1, QTableWidgetItem(device.mac_address))
            self.devices_table.setItem(
                row, 2,
                QTableWidgetItem(device.hostname or "Unknown")
            )
            self.devices_table.setItem(
                row, 3,
                QTableWidgetItem(device.last_seen.strftime("%Y-%m-%d %H:%M:%S"))
            )
            
    def scan_network(self):
        """Trigger network scan"""
        # This should be implemented to trigger NetworkMapper scan

class SecurityAlertsWidget(QWidget):
    """Widget for displaying security alerts"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # Alerts table
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(4)
        self.alerts_table.setHorizontalHeaderLabels([
            "Time", "Level", "Source", "Message"
        ])
        header = self.alerts_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.alerts_table)
        
        self.setLayout(layout)
        self.alerts = []
        
    def add_alert(self, level: str, source: str, message: str):
        """Add new security alert"""
        alert = {
            "time": datetime.now(),
            "level": level,
            "source": source,
            "message": message
        }
        self.alerts.append(alert)
        self._update_table()
        
    def get_active_alerts(self) -> List[Dict]:
        """Get list of active alerts"""
        return self.alerts
        
    def _update_table(self):
        """Update alerts table"""
        self.alerts_table.setRowCount(len(self.alerts))
        for row, alert in enumerate(self.alerts):
            self.alerts_table.setItem(
                row, 0,
                QTableWidgetItem(alert["time"].strftime("%Y-%m-%d %H:%M:%S"))
            )
            self.alerts_table.setItem(row, 1, QTableWidgetItem(alert["level"]))
            self.alerts_table.setItem(row, 2, QTableWidgetItem(alert["source"]))
            self.alerts_table.setItem(row, 3, QTableWidgetItem(alert["message"]))
            
            # Color code by level
            color = {
                "LOW": QColor(255, 255, 200),    # Light yellow
                "MEDIUM": QColor(255, 200, 100),  # Light orange
                "HIGH": QColor(255, 200, 200)     # Light red
            }.get(alert["level"])
            
            if color:
                for col in range(4):
                    item = self.alerts_table.item(row, col)
                    item.setBackground(color)

class PluginsWidget(QWidget):
    """Widget for managing plugins"""
    
    def __init__(self, plugin_loader: PluginLoader):
        super().__init__()
        self.plugin_loader = plugin_loader
        
        layout = QVBoxLayout()
        
        # Plugins table
        self.plugins_table = QTableWidget()
        self.plugins_table.setColumnCount(5)
        self.plugins_table.setHorizontalHeaderLabels([
            "Name", "Version", "Author", "Status", "Actions"
        ])
        header = self.plugins_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.plugins_table)
        
        # Reload button
        reload_button = QPushButton("Reload Plugins")
        reload_button.clicked.connect(self.reload_plugins)
        layout.addWidget(reload_button)
        
        self.setLayout(layout)
        
    def update_plugins(self):
        """Update plugin list"""
        available_plugins = self.plugin_loader.get_available_plugins()
        active_plugins = self.plugin_loader.get_active_plugins()
        
        self.plugins_table.setRowCount(len(available_plugins))
        for row, name in enumerate(available_plugins):
            plugin_class = self.plugin_loader.plugins[name]
            
            self.plugins_table.setItem(row, 0, QTableWidgetItem(plugin_class.name))
            self.plugins_table.setItem(row, 1, QTableWidgetItem(plugin_class.version))
            self.plugins_table.setItem(row, 2, QTableWidgetItem(plugin_class.author))
            
            status = "Active" if name in active_plugins else "Inactive"
            self.plugins_table.setItem(row, 3, QTableWidgetItem(status))
            
            # Add action button
            action_button = QPushButton(
                "Deactivate" if name in active_plugins else "Activate"
            )
            action_button.clicked.connect(
                lambda checked, n=name: self.toggle_plugin(n)
            )
            self.plugins_table.setCellWidget(row, 4, action_button)
            
    def toggle_plugin(self, name: str):
        """Toggle plugin activation state"""
        try:
            if name in self.plugin_loader.get_active_plugins():
                self.plugin_loader.deactivate_plugin(name)
            else:
                self.plugin_loader.activate_plugin(name)
            self.update_plugins()
        except Exception as e:
            # Show error dialog
            pass
            
    def reload_plugins(self):
        """Reload all plugins"""
        try:
            self.plugin_loader.reload_plugins()
            self.update_plugins()
        except Exception as e:
            # Show error dialog
            pass
