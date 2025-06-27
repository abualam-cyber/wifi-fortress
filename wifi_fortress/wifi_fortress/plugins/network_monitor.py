from ..core.plugin_loader import Plugin
from ..utils.network_utils import (
    get_network_interfaces,
    get_wifi_signal_strength,
    get_network_usage,
    format_bytes
)
from ..gui.dashboard import SecurityAlertsWidget, DashboardWidget
from PyQt5.QtWidgets import QApplication, QMainWindow
from threading import Thread, Event
import time
from typing import Dict, List
import logging
import json

class NetworkMonitor(Plugin):
    name = 'Network Monitor'
    description = 'Monitors network interfaces and usage'
    version = '1.0.0'
    author = 'WiFi Fortress Team'
    
    def __init__(self):
        super().__init__()
        self.interfaces: List[Dict] = []
        self.monitor_thread = None
        self.stop_event = Event()
        self.interface_stats: Dict[str, Dict] = {}
        self.alert_thresholds = {
            'signal_strength': 30,  # Alert if signal strength below 30%
            'error_rate': 0.01,    # Alert if error rate above 1%
            'dropout_rate': 0.01   # Alert if dropout rate above 1%
        }
        self.alerts_widget = None
        
    def initialize(self) -> bool:
        """Initialize the network monitor"""
        try:
            # Get network interfaces
            self.interfaces = get_network_interfaces()
            if not self.interfaces:
                self.logger.warning("No network interfaces found")
                return False
                
            # Find dashboard alerts widget
            app = QApplication.instance()
            if app:
                for widget in app.topLevelWidgets():
                    if isinstance(widget, QMainWindow):
                        dashboard = widget.findChild(DashboardWidget)
                        if dashboard:
                            self.alerts_widget = dashboard.alerts_widget
                            break
                            
            # Start monitoring
            self.start_monitoring()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize network monitor: {str(e)}")
            return False
            
    def start_monitoring(self):
        """Start monitoring network interfaces"""
        if not self.enabled or self.monitor_thread:
            return
            
        def monitor_worker():
            while not self.stop_event.is_set():
                try:
                    for interface in self.interfaces:
                        iface_name = interface['name']
                        
                        # Get current stats
                        usage = get_network_usage(iface_name)
                        signal = get_wifi_signal_strength(iface_name)
                        
                        # Calculate rates and store stats
                        if iface_name in self.interface_stats:
                            prev_stats = self.interface_stats[iface_name]
                            total_packets = (usage['packets_sent'] + usage['packets_recv'] - 
                                          prev_stats['packets_sent'] - prev_stats['packets_recv'])
                            
                            if total_packets > 0:
                                error_rate = (usage['errin'] + usage['errout'] - 
                                            prev_stats['errin'] - prev_stats['errout']) / total_packets
                                dropout_rate = (usage['dropin'] + usage['dropout'] - 
                                              prev_stats['dropin'] - prev_stats['dropout']) / total_packets
                                
                                # Check thresholds and generate alerts
                                self.check_thresholds(iface_name, {
                                    'signal_strength': signal,
                                    'error_rate': error_rate,
                                    'dropout_rate': dropout_rate
                                })
                        
                        # Update stats
                        self.interface_stats[iface_name] = {
                            'timestamp': time.time(),
                            'signal_strength': signal,
                            **usage
                        }
                        
                        # Log current status
                        self.log_interface_status(iface_name)
                        
                    time.sleep(5)  # Update every 5 seconds
                except Exception as e:
                    self.logger.error(f"Error in monitor worker: {str(e)}")
                    time.sleep(10)  # Wait longer on error
                    
        self.monitor_thread = Thread(target=monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def check_thresholds(self, interface: str, metrics: Dict):
        """Check if any metrics exceed their thresholds"""
        if not metrics:
            return
            
        # Check signal strength
        if metrics.get('signal_strength') is not None:
            if metrics['signal_strength'] < self.alert_thresholds['signal_strength']:
                self.add_alert(
                    'HIGH',
                    f'Low signal strength on {interface}: {metrics["signal_strength"]}%'
                )
                
        # Check error rate
        if metrics.get('error_rate') is not None:
            if metrics['error_rate'] > self.alert_thresholds['error_rate']:
                self.add_alert(
                    'MEDIUM',
                    f'High error rate on {interface}: {metrics["error_rate"]:.2%}'
                )
                
        # Check dropout rate
        if metrics.get('dropout_rate') is not None:
            if metrics['dropout_rate'] > self.alert_thresholds['dropout_rate']:
                self.add_alert(
                    'MEDIUM',
                    f'High packet dropout on {interface}: {metrics["dropout_rate"]:.2%}'
                )
                
    def add_alert(self, level: str, message: str):
        """Add alert to dashboard"""
        if self.alerts_widget:
            self.alerts_widget.add_alert(level, self.name, message)
        self.logger.warning(f"{level} alert: {message}")
        
    def log_interface_status(self, interface: str):
        """Log current interface status"""
        stats = self.interface_stats[interface]
        status = {
            'interface': interface,
            'signal_strength': stats['signal_strength'],
            'bytes_sent': format_bytes(stats['bytes_sent']),
            'bytes_recv': format_bytes(stats['bytes_recv']),
            'errors': stats['errin'] + stats['errout'],
            'drops': stats['dropin'] + stats['dropout']
        }
        self.logger.info(json.dumps(status, indent=2))

    def cleanup(self) -> bool:
        """Stop monitoring and cleanup"""
        self.enabled = False
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.monitor_thread = None
        return True
