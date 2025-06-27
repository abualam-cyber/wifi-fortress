import pytest
import time
from unittest.mock import Mock, patch
from wifi_fortress.plugins.performance_monitor import PerformanceMonitor, NetworkStats

@pytest.fixture
def performance_monitor():
    return PerformanceMonitor()

def test_performance_monitor_init(performance_monitor):
    """Test performance monitor initialization"""
    assert performance_monitor.name == 'Performance Monitor'
    assert performance_monitor.version == '1.0.0'
    assert performance_monitor.enabled
    
    # Test initialization
    with patch('psutil.net_if_stats') as mock_stats:
        mock_stats.return_value = {'eth0': Mock(), 'wlan0': Mock()}
        assert performance_monitor.initialize()
        assert len(performance_monitor._stats_history) == 2
        assert 'eth0' in performance_monitor._stats_history
        assert 'wlan0' in performance_monitor._stats_history

def test_monitor_loop(performance_monitor):
    """Test monitoring loop"""
    # Mock network stats
    mock_stats = {
        'eth0': Mock(
            bytes_sent=1000,
            bytes_recv=2000,
            packets_sent=100,
            packets_recv=200,
            errin=1,
            errout=2,
            dropin=3,
            dropout=4
        )
    }
    
    with patch('psutil.net_io_counters', return_value=mock_stats):
        # Initialize monitor
        performance_monitor.initialize()
        
        # Let it run for a bit
        time.sleep(2)
        
        # Check collected stats
        stats = performance_monitor.get_interface_stats('eth0', duration=1)
        assert len(stats) > 0
        
        # Verify stats content
        latest_stat = stats[-1]
        assert isinstance(latest_stat, NetworkStats)
        assert latest_stat.bytes_sent >= 0
        assert latest_stat.bytes_recv >= 0
        assert latest_stat.packets_sent >= 0
        assert latest_stat.packets_recv >= 0

def test_cleanup(performance_monitor):
    """Test cleanup"""
    performance_monitor.initialize()
    assert performance_monitor.cleanup()
    assert not performance_monitor._monitor_thread.is_alive()

def test_get_interface_stats(performance_monitor):
    """Test getting interface statistics"""
    # Initialize with mock data
    with patch('psutil.net_if_stats') as mock_stats:
        mock_stats.return_value = {'eth0': Mock()}
        performance_monitor.initialize()
        
        # Add some test stats
        test_stats = NetworkStats()
        test_stats.bytes_sent = 1000
        test_stats.bytes_recv = 2000
        
        with performance_monitor._lock:
            performance_monitor._stats_history['eth0'].append(test_stats)
        
        # Get stats
        stats = performance_monitor.get_interface_stats('eth0', duration=60)
        assert len(stats) > 0
        assert isinstance(stats[0], NetworkStats)
        
        # Test nonexistent interface
        assert performance_monitor.get_interface_stats('invalid') == []

def test_get_current_bandwidth(performance_monitor):
    """Test bandwidth calculation"""
    # Initialize with mock data
    with patch('psutil.net_if_stats') as mock_stats:
        mock_stats.return_value = {'eth0': Mock()}
        performance_monitor.initialize()
        
        # Add test stats
        test_stats = NetworkStats()
        test_stats.bytes_sent = 1_000_000  # 1 MB
        test_stats.bytes_recv = 2_000_000  # 2 MB
        
        with performance_monitor._lock:
            performance_monitor._stats_history['eth0'].append(test_stats)
        
        # Get bandwidth
        bandwidth = performance_monitor.get_current_bandwidth('eth0')
        assert isinstance(bandwidth, dict)
        assert 'rx_mbps' in bandwidth
        assert 'tx_mbps' in bandwidth
        assert bandwidth['rx_mbps'] > 0
        assert bandwidth['tx_mbps'] > 0
        
        # Test nonexistent interface
        bandwidth = performance_monitor.get_current_bandwidth('invalid')
        assert bandwidth['rx_mbps'] == 0
        assert bandwidth['tx_mbps'] == 0

def test_alert_thresholds(performance_monitor):
    """Test alert threshold management"""
    # Set thresholds
    assert performance_monitor.set_alert_threshold('error_rate', 0.05)
    assert performance_monitor.set_alert_threshold('drop_rate', 0.05)
    assert performance_monitor.set_alert_threshold('latency_ms', 50)
    
    # Invalid threshold
    assert not performance_monitor.set_alert_threshold('invalid', 0.1)
    
    # Check threshold values
    assert performance_monitor._alert_thresholds['error_rate'] == 0.05
    assert performance_monitor._alert_thresholds['drop_rate'] == 0.05
    assert performance_monitor._alert_thresholds['latency_ms'] == 50

def test_thread_safety(performance_monitor):
    """Test thread safety of stats collection"""
    import threading
    
    # Initialize monitor
    with patch('psutil.net_if_stats') as mock_stats:
        mock_stats.return_value = {'eth0': Mock()}
        performance_monitor.initialize()
        
        # Function to simulate concurrent access
        def concurrent_access():
            for _ in range(100):
                stats = performance_monitor.get_interface_stats('eth0')
                bandwidth = performance_monitor.get_current_bandwidth('eth0')
        
        # Create multiple threads
        threads = [
            threading.Thread(target=concurrent_access)
            for _ in range(5)
        ]
        
        # Run threads
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # If we got here without exceptions, thread safety worked
