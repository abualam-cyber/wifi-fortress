import pytest
from datetime import datetime, timedelta
from wifi_fortress.plugins.intrusion_detector import IntrusionDetector, IntrusionEvent

@pytest.fixture
def intrusion_detector():
    return IntrusionDetector()

def test_intrusion_detector_init(intrusion_detector):
    """Test intrusion detector initialization"""
    assert intrusion_detector.name == 'Intrusion Detector'
    assert intrusion_detector.version == '1.0.0'
    assert intrusion_detector.enabled
    assert intrusion_detector.initialize()

def test_analyze_connection(intrusion_detector):
    """Test connection analysis"""
    # Test normal connection
    mac = '00:11:22:33:44:55'
    ip = '192.168.1.100'
    
    intrusion_detector.analyze_connection(mac, ip)
    events = intrusion_detector.get_recent_events(minutes=5)
    assert len(events) == 1
    assert events[0].event_type == 'DeviceWhitelisted'
    
    # Test blacklisted device
    intrusion_detector.blacklist_device(mac, 'Test blacklist')
    intrusion_detector.analyze_connection(mac, ip)
    
    events = intrusion_detector.get_recent_events(minutes=5)
    assert any(e.event_type == 'BlacklistedDeviceAttempt' for e in events)

def test_excessive_connections(intrusion_detector):
    """Test excessive connection detection"""
    mac = '00:11:22:33:44:55'
    ip = '192.168.1.100'
    
    # Make multiple connection attempts
    for _ in range(intrusion_detector._max_connection_attempts + 1):
        intrusion_detector.analyze_connection(mac, ip)
    
    # Check if device was blacklisted
    assert mac in intrusion_detector._blacklist
    
    events = intrusion_detector.get_recent_events(minutes=5)
    assert any(e.event_type == 'ExcessiveConnectionAttempts' for e in events)

def test_blacklist_whitelist(intrusion_detector):
    """Test blacklist and whitelist functionality"""
    mac = '00:11:22:33:44:55'
    
    # Test blacklisting
    intrusion_detector.blacklist_device(mac, 'Test reason')
    assert mac in intrusion_detector._blacklist
    
    events = intrusion_detector.get_recent_events(minutes=5)
    assert any(e.event_type == 'DeviceBlacklisted' for e in events)
    
    # Test whitelisting
    intrusion_detector.whitelist_device(mac)
    assert mac not in intrusion_detector._blacklist
    assert mac in intrusion_detector._known_devices
    
    events = intrusion_detector.get_recent_events(minutes=5)
    assert any(e.event_type == 'DeviceWhitelisted' for e in events)

def test_suspicious_signal_strength(intrusion_detector):
    """Test suspicious signal strength detection"""
    mac = '00:11:22:33:44:55'
    ip = '192.168.1.100'
    
    # Test with very weak signal
    intrusion_detector.analyze_connection(mac, ip, rssi=-95)
    
    events = intrusion_detector.get_recent_events(minutes=5)
    assert any(e.event_type == 'SuspiciousSignalStrength' for e in events)
    
    # Test with normal signal
    intrusion_detector.analyze_connection(mac, ip, rssi=-65)
    events = intrusion_detector.get_recent_events(minutes=1)
    assert not any(e.event_type == 'SuspiciousSignalStrength' for e in events)

def test_event_management(intrusion_detector):
    """Test event management"""
    # Add test events
    for i in range(10):
        event = IntrusionEvent('TestEvent', f'source{i}', {'test': i})
        intrusion_detector._events.append(event)
    
    # Test recent events filtering
    recent = intrusion_detector.get_recent_events(minutes=5)
    assert len(recent) == 10
    
    # Make some events old
    old_time = datetime.now() - timedelta(minutes=10)
    for event in intrusion_detector._events[:5]:
        event.timestamp = old_time
    
    recent = intrusion_detector.get_recent_events(minutes=5)
    assert len(recent) == 5

def test_cleanup(intrusion_detector):
    """Test cleanup"""
    # Add some test data
    mac = '00:11:22:33:44:55'
    intrusion_detector.blacklist_device(mac, 'Test')
    intrusion_detector._events.append(
        IntrusionEvent('TestEvent', mac, {})
    )
    
    # Cleanup
    assert intrusion_detector.cleanup()
    assert len(intrusion_detector._events) == 0
    assert len(intrusion_detector._blacklist) == 0
    assert len(intrusion_detector._known_devices) == 0

def test_connection_window(intrusion_detector):
    """Test connection attempt window"""
    mac = '00:11:22:33:44:55'
    ip = '192.168.1.100'
    
    # Make some old attempts
    old_time = datetime.now() - timedelta(seconds=intrusion_detector._connection_window + 10)
    for _ in range(3):
        intrusion_detector._connection_attempts[mac].append(old_time)
    
    # Make some new attempts
    for _ in range(3):
        intrusion_detector.analyze_connection(mac, ip)
    
    # Should only count recent attempts
    assert len(intrusion_detector._connection_attempts[mac]) == 3
    
    # Add more attempts to trigger blacklist
    for _ in range(3):
        intrusion_detector.analyze_connection(mac, ip)
    
    assert mac in intrusion_detector._blacklist
