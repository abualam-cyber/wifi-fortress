import logging
import psutil
import threading
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque

from .error_handler import handle_errors, NetworkError

logger = logging.getLogger(__name__)

class HealthMetrics:
    """Container for system health metrics"""
    
    def __init__(self):
        self.cpu_percent: float = 0.0
        self.memory_percent: float = 0.0
        self.disk_usage: Dict[str, float] = {}
        self.network_io: Dict[str, Dict[str, int]] = {}
        self.thread_count: int = 0
        self.open_files: int = 0
        self.timestamp: datetime = datetime.now()
        
class HealthStatus:
    """System health status"""
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class HealthMonitor:
    """System health monitoring for WiFi Fortress"""
    
    def __init__(self, history_size: int = 60):
        self._metrics_history = deque(maxlen=history_size)
        self._lock = threading.Lock()
        self._stop_monitoring = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Thresholds
        self.cpu_warning_threshold = 70.0
        self.cpu_critical_threshold = 90.0
        self.memory_warning_threshold = 80.0
        self.memory_critical_threshold = 95.0
        self.disk_warning_threshold = 80.0
        self.disk_critical_threshold = 95.0
        
    @handle_errors(error_types=(psutil.Error, Exception))
    def collect_metrics(self) -> HealthMetrics:
        """Collect current system health metrics
        
        Returns:
            HealthMetrics: Current system metrics
        """
        metrics = HealthMetrics()
        
        # CPU usage
        metrics.cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        metrics.memory_percent = memory.percent
        
        # Disk usage
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                metrics.disk_usage[partition.mountpoint] = usage.percent
            except Exception as e:
                logger.warning(f'Error getting disk usage for {partition.mountpoint}: {e}')
                
        # Network I/O
        net_io = psutil.net_io_counters(pernic=True)
        for interface, counters in net_io.items():
            metrics.network_io[interface] = {
                'bytes_sent': counters.bytes_sent,
                'bytes_recv': counters.bytes_recv,
                'packets_sent': counters.packets_sent,
                'packets_recv': counters.packets_recv,
                'errin': counters.errin,
                'errout': counters.errout,
                'dropin': counters.dropin,
                'dropout': counters.dropout
            }
            
        # Process metrics
        process = psutil.Process()
        metrics.thread_count = process.num_threads()
        metrics.open_files = len(process.open_files())
        
        return metrics
        
    def start_monitoring(self, interval: int = 60) -> None:
        """Start continuous health monitoring
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitor_thread and self._monitor_thread.is_alive():
            raise RuntimeError('Monitoring already running')
            
        def _monitor_loop():
            while not self._stop_monitoring.is_set():
                try:
                    metrics = self.collect_metrics()
                    with self._lock:
                        self._metrics_history.append(metrics)
                except Exception as e:
                    logger.error(f'Error collecting metrics: {e}')
                finally:
                    self._stop_monitoring.wait(interval)
                    
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(
            target=_monitor_loop,
            name='health_monitor'
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        logger.info('Health monitoring started')
        
    def stop_monitoring(self, timeout: int = 10) -> bool:
        """Stop health monitoring
        
        Args:
            timeout: Maximum time to wait for thread completion
            
        Returns:
            bool: True if monitoring was stopped
        """
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._stop_monitoring.set()
            self._monitor_thread.join(timeout=timeout)
            return not self._monitor_thread.is_alive()
        return True
        
    def get_current_status(self) -> str:
        """Get current system health status
        
        Returns:
            str: Current status (OK, WARNING, CRITICAL)
        """
        try:
            metrics = self.collect_metrics()
            
            # Check CPU
            if metrics.cpu_percent >= self.cpu_critical_threshold:
                return HealthStatus.CRITICAL
            elif metrics.cpu_percent >= self.cpu_warning_threshold:
                return HealthStatus.WARNING
                
            # Check memory
            if metrics.memory_percent >= self.memory_critical_threshold:
                return HealthStatus.CRITICAL
            elif metrics.memory_percent >= self.memory_warning_threshold:
                return HealthStatus.WARNING
                
            # Check disk
            for usage in metrics.disk_usage.values():
                if usage >= self.disk_critical_threshold:
                    return HealthStatus.CRITICAL
                elif usage >= self.disk_warning_threshold:
                    return HealthStatus.WARNING
                    
            return HealthStatus.OK
            
        except Exception as e:
            logger.error(f'Error getting health status: {e}')
            return HealthStatus.CRITICAL
            
    def get_metrics_history(self,
                          duration: timedelta = timedelta(minutes=60)
                          ) -> List[HealthMetrics]:
        """Get metrics history for specified duration
        
        Args:
            duration: Time duration to retrieve
            
        Returns:
            List[HealthMetrics]: List of metrics within duration
        """
        with self._lock:
            cutoff_time = datetime.now() - duration
            return [
                m for m in self._metrics_history
                if m.timestamp >= cutoff_time
            ]
            
    def get_network_errors(self) -> Dict[str, Dict[str, int]]:
        """Get network error counts by interface
        
        Returns:
            Dict: Network errors and drops by interface
        """
        try:
            metrics = self.collect_metrics()
            errors = {}
            
            for interface, io in metrics.network_io.items():
                errors[interface] = {
                    'errors': io['errin'] + io['errout'],
                    'drops': io['dropin'] + io['dropout']
                }
                
            return errors
            
        except Exception as e:
            logger.error(f'Error getting network errors: {e}')
            return {}
