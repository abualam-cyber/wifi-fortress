import psutil
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
from threading import Lock, Thread, Event
from wifi_fortress.core.plugin_loader import Plugin

logger = logging.getLogger(__name__)

class NetworkStats:
    def __init__(self):
        self.timestamp = datetime.now()
        self.bytes_sent = 0
        self.bytes_recv = 0
        self.packets_sent = 0
        self.packets_recv = 0
        self.errin = 0
        self.errout = 0
        self.dropin = 0
        self.dropout = 0

class PerformanceMonitor(Plugin):
    """Network performance monitoring plugin"""
    
    name = 'Performance Monitor'
    description = 'Monitors network performance metrics'
    version = '1.0.0'
    author = 'WiFi Fortress Team'
    
    def __init__(self):
        super().__init__()
        self._stats_history: Dict[str, deque] = {}  # Interface -> stats history
        self._lock = Lock()
        self._stop_monitoring = Event()
        self._monitor_thread: Optional[Thread] = None
        self._history_length = 3600  # Keep 1 hour of history (1 sample per second)
        self._alert_thresholds = {
            'error_rate': 0.01,  # 1% error rate
            'drop_rate': 0.01,   # 1% drop rate
            'latency_ms': 100    # 100ms latency
        }
        
    def initialize(self) -> bool:
        """Initialize performance monitoring"""
        try:
            # Initialize stats for all network interfaces
            for interface in psutil.net_if_stats().keys():
                self._stats_history[interface] = deque(maxlen=self._history_length)
            
            # Start monitoring thread
            self._stop_monitoring.clear()
            self._monitor_thread = Thread(
                target=self._monitor_loop,
                name='performance_monitor'
            )
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
            
            logger.info('Performance monitoring initialized')
            return True
        except Exception as e:
            logger.error(f'Failed to initialize performance monitoring: {e}')
            return False
            
    def cleanup(self) -> bool:
        """Stop monitoring and cleanup"""
        try:
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._stop_monitoring.set()
                self._monitor_thread.join(timeout=5)
            return True
        except Exception as e:
            logger.error(f'Error during cleanup: {e}')
            return False
            
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        last_check = {}
        while not self._stop_monitoring.is_set():
            try:
                current_stats = psutil.net_io_counters(pernic=True)
                current_time = datetime.now()
                
                for interface, stats in current_stats.items():
                    if interface not in self._stats_history:
                        continue
                        
                    # Calculate rates if we have previous measurements
                    if interface in last_check:
                        last_time, last_stats = last_check[interface]
                        time_diff = (current_time - last_time).total_seconds()
                        
                        if time_diff > 0:
                            network_stats = NetworkStats()
                            network_stats.timestamp = current_time
                            network_stats.bytes_sent = (stats.bytes_sent - last_stats.bytes_sent) / time_diff
                            network_stats.bytes_recv = (stats.bytes_recv - last_stats.bytes_recv) / time_diff
                            network_stats.packets_sent = (stats.packets_sent - last_stats.packets_sent) / time_diff
                            network_stats.packets_recv = (stats.packets_recv - last_stats.packets_recv) / time_diff
                            network_stats.errin = stats.errin - last_stats.errin
                            network_stats.errout = stats.errout - last_stats.errout
                            network_stats.dropin = stats.dropin - last_stats.dropin
                            network_stats.dropout = stats.dropout - last_stats.dropout
                            
                            with self._lock:
                                self._stats_history[interface].append(network_stats)
                            
                            # Check for alerts
                            self._check_alerts(interface, network_stats)
                    
                    # Update last check
                    last_check[interface] = (current_time, stats)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f'Error in performance monitoring: {e}')
                time.sleep(5)  # Wait before retrying
                
    def _check_alerts(self, interface: str, stats: NetworkStats) -> None:
        """Check performance metrics against thresholds"""
        try:
            # Calculate error rate
            total_packets = stats.packets_sent + stats.packets_recv
            if total_packets > 0:
                error_rate = (stats.errin + stats.errout) / total_packets
                if error_rate > self._alert_thresholds['error_rate']:
                    logger.warning(
                        f'High error rate on {interface}: {error_rate:.2%}'
                    )
            
            # Calculate drop rate
            if total_packets > 0:
                drop_rate = (stats.dropin + stats.dropout) / total_packets
                if drop_rate > self._alert_thresholds['drop_rate']:
                    logger.warning(
                        f'High packet drop rate on {interface}: {drop_rate:.2%}'
                    )
                    
        except Exception as e:
            logger.error(f'Error checking alerts: {e}')
            
    def get_interface_stats(self, interface: str, 
                           duration: int = 300) -> List[NetworkStats]:
        """Get interface statistics for the specified duration
        
        Args:
            interface: Network interface name
            duration: Duration in seconds (default: 5 minutes)
            
        Returns:
            List of NetworkStats objects
        """
        with self._lock:
            if interface not in self._stats_history:
                return []
                
            cutoff_time = datetime.now() - timedelta(seconds=duration)
            return [
                stat for stat in self._stats_history[interface]
                if stat.timestamp >= cutoff_time
            ]
            
    def get_current_bandwidth(self, interface: str) -> Dict[str, float]:
        """Get current bandwidth usage for interface
        
        Args:
            interface: Network interface name
            
        Returns:
            Dict with 'rx_mbps' and 'tx_mbps' keys
        """
        with self._lock:
            if interface not in self._stats_history or not self._stats_history[interface]:
                return {'rx_mbps': 0.0, 'tx_mbps': 0.0}
                
            latest = self._stats_history[interface][-1]
            return {
                'rx_mbps': (latest.bytes_recv * 8) / 1_000_000,  # Convert to Mbps
                'tx_mbps': (latest.bytes_sent * 8) / 1_000_000
            }
            
    def set_alert_threshold(self, metric: str, value: float) -> bool:
        """Set alert threshold for a metric
        
        Args:
            metric: Metric name ('error_rate', 'drop_rate', 'latency_ms')
            value: Threshold value
            
        Returns:
            bool: True if threshold was set
        """
        if metric in self._alert_thresholds:
            self._alert_thresholds[metric] = value
            return True
        return False
