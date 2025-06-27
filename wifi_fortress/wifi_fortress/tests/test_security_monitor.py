import pytest
from datetime import datetime, timedelta
from wifi_fortress.plugins.security_monitor import SecurityMonitor

@pytest.fixture
def security_monitor():
    return SecurityMonitor()

def test_security_monitor_init(security_monitor):
    """Test security monitor initialization"""
    assert security_monitor.name == 'Security Monitor'
    assert security_monitor.version == '1.0.0'
    assert security_monitor.enabled
    assert security_monitor.initialize()

def test_analyze_device(security_monitor):
    """Test device analysis"""
    # Test new device detection
    security_monitor.analyze_device('00:11:22:33:44:55', '192.168.1.100')
    assert len(security_monitor._known_devices) == 1
    assert len(security_monitor._suspicious_activity) == 1
    assert security_monitor._suspicious_activity[0]['type'] == 'New device detected'

def test_clean_old_events(security_monitor):
    """Test event cleanup"""
    # Add old event
    old_time = datetime.now() - timedelta(hours=2)
    security_monitor._suspicious_activity.append({
        'type': 'Test Event',
        'details': {},
        'timestamp': old_time
    })
    
    # Add recent event
    security_monitor._suspicious_activity.append({
        'type': 'Test Event',
        'details': {},
        'timestamp': datetime.now()
    })
    
    # Clean events
    security_monitor._clean_old_events()
    assert len(security_monitor._suspicious_activity) == 1
    assert security_monitor._suspicious_activity[0]['timestamp'] > old_time

def test_security_alert_threshold(security_monitor):
    """Test security alert threshold"""
    # Add multiple events
    for i in range(security_monitor._alert_threshold):
        security_monitor._log_security_event(
            'Test Event',
            {'test_id': i}
        )
    
    # Should have triggered alert
    assert len(security_monitor._suspicious_activity) >= security_monitor._alert_threshold

def test_cleanup(security_monitor):
    """Test cleanup"""
    # Add some data
    security_monitor.analyze_device('00:11:22:33:44:55', '192.168.1.100')
    assert len(security_monitor._known_devices) > 0
    assert len(security_monitor._suspicious_activity) > 0
    
    # Cleanup
    assert security_monitor.cleanup()
    assert len(security_monitor._known_devices) == 0
    assert len(security_monitor._suspicious_activity) == 0
