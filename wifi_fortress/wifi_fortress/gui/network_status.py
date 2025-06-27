from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QProgressBar, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette
import psutil
import time
from typing import Dict, Optional
from wifi_fortress.plugins.performance_monitor import PerformanceMonitor

class NetworkStatusWidget(QWidget):
    """Widget displaying real-time network status"""
    
    def __init__(self, performance_monitor: Optional[PerformanceMonitor] = None,
                 parent=None):
        super().__init__(parent)
        self.performance_monitor = performance_monitor
        self._setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # Update every second
        
    def _setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Network Status')
        title.setStyleSheet('font-size: 14px; font-weight: bold;')
        layout.addWidget(title)
        
        # Stats frame
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        stats_layout = QVBoxLayout()
        
        # Interface stats
        self.interface_widgets: Dict[str, Dict] = {}
        
        for interface, _ in psutil.net_if_stats().items():
            # Interface group
            interface_group = QFrame()
            interface_layout = QVBoxLayout()
            
            # Interface name
            name_label = QLabel(f'<b>{interface}</b>')
            interface_layout.addWidget(name_label)
            
            # Bandwidth
            bandwidth_layout = QHBoxLayout()
            bandwidth_layout.addWidget(QLabel('Bandwidth:'))
            rx_label = QLabel('RX: 0 Mbps')
            tx_label = QLabel('TX: 0 Mbps')
            bandwidth_layout.addWidget(rx_label)
            bandwidth_layout.addWidget(tx_label)
            interface_layout.addLayout(bandwidth_layout)
            
            # Error rate
            error_layout = QHBoxLayout()
            error_layout.addWidget(QLabel('Error Rate:'))
            error_bar = QProgressBar()
            error_bar.setRange(0, 100)
            error_bar.setValue(0)
            error_layout.addWidget(error_bar)
            interface_layout.addLayout(error_layout)
            
            # Drop rate
            drop_layout = QHBoxLayout()
            drop_layout.addWidget(QLabel('Drop Rate:'))
            drop_bar = QProgressBar()
            drop_bar.setRange(0, 100)
            drop_bar.setValue(0)
            drop_layout.addWidget(drop_bar)
            interface_layout.addLayout(drop_layout)
            
            interface_group.setLayout(interface_layout)
            stats_layout.addWidget(interface_group)
            
            # Store widgets for updates
            self.interface_widgets[interface] = {
                'rx_label': rx_label,
                'tx_label': tx_label,
                'error_bar': error_bar,
                'drop_bar': drop_bar
            }
            
        stats_frame.setLayout(stats_layout)
        layout.addWidget(stats_frame)
        
        # Status message
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def update_stats(self):
        """Update network statistics"""
        try:
            for interface, widgets in self.interface_widgets.items():
                if self.performance_monitor:
                    # Get stats from performance monitor
                    bandwidth = self.performance_monitor.get_current_bandwidth(interface)
                    widgets['rx_label'].setText(f'RX: {bandwidth["rx_mbps"]:.1f} Mbps')
                    widgets['tx_label'].setText(f'TX: {bandwidth["tx_mbps"]:.1f} Mbps')
                    
                    # Get recent stats for error and drop rates
                    stats = self.performance_monitor.get_interface_stats(interface, 60)
                    if stats:
                        total_packets = sum(s.packets_sent + s.packets_recv for s in stats)
                        if total_packets > 0:
                            error_rate = sum(s.errin + s.errout for s in stats) / total_packets
                            drop_rate = sum(s.dropin + s.dropout for s in stats) / total_packets
                            
                            widgets['error_bar'].setValue(int(error_rate * 100))
                            widgets['drop_bar'].setValue(int(drop_rate * 100))
                            
                            # Update bar colors based on rates
                            self._update_bar_color(widgets['error_bar'], error_rate)
                            self._update_bar_color(widgets['drop_bar'], drop_rate)
                else:
                    # Fallback to basic psutil stats
                    stats = psutil.net_io_counters(pernic=True).get(interface)
                    if stats:
                        widgets['rx_label'].setText(
                            f'RX: {stats.bytes_recv / 1_000_000:.1f} MB'
                        )
                        widgets['tx_label'].setText(
                            f'TX: {stats.bytes_sent / 1_000_000:.1f} MB'
                        )
                        
            self.status_label.setText('Status: Connected')
            self.status_label.setStyleSheet('color: green;')
            
        except Exception as e:
            self.status_label.setText(f'Error updating stats: {str(e)}')
            self.status_label.setStyleSheet('color: red;')
            
    def _update_bar_color(self, bar: QProgressBar, rate: float):
        """Update progress bar color based on rate"""
        if rate > 0.1:  # > 10%
            color = QColor(255, 0, 0)  # Red
        elif rate > 0.05:  # > 5%
            color = QColor(255, 165, 0)  # Orange
        else:
            color = QColor(0, 255, 0)  # Green
            
        palette = bar.palette()
        palette.setColor(QPalette.Highlight, color)
        bar.setPalette(palette)
        
    def showEvent(self, event):
        """Start updates when widget is shown"""
        super().showEvent(event)
        self.update_timer.start()
        
    def hideEvent(self, event):
        """Stop updates when widget is hidden"""
        super().hideEvent(event)
        self.update_timer.stop()
