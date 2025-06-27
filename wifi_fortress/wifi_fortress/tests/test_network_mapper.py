import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from cryptography.fernet import Fernet
from wifi_fortress.core.network_mapper import NetworkMapper, NetworkDevice

@pytest.fixture
def encryption_key():
    return Fernet.generate_key().decode()

@pytest.fixture
def network_mapper(encryption_key):
    return NetworkMapper(encryption_key=encryption_key)

@pytest.fixture
def mock_network_device():
    return NetworkDevice(
        ip_address='192.168.1.1',
        mac_address='00:11:22:33:44:55'
    )

def test_network_device_creation():
    device = NetworkDevice(
        ip_address='192.168.1.1',
        mac_address='00:11:22:33:44:55'
    )
    assert device.ip_address == '192.168.1.1'
    assert device.mac_address == '00:11:22:33:44:55'
    assert device.is_active is True
    assert isinstance(device.first_seen, datetime)
    assert isinstance(device.last_seen, datetime)

def test_encryption(network_mapper, mock_network_device):
    """Test device data encryption"""
    # Test encryption
    network_mapper._encrypt_device_data(mock_network_device)
    assert mock_network_device.mac_address != '00:11:22:33:44:55'
    
    # Test decryption
    network_mapper._decrypt_device_data(mock_network_device)
    assert mock_network_device.mac_address == '00:11:22:33:44:55'

@patch('netifaces.interfaces')
@patch('netifaces.ifaddresses')
def test_get_network_interfaces(mock_ifaddresses, mock_interfaces, network_mapper):
    mock_interfaces.return_value = ['eth0']
    mock_ifaddresses.return_value = {
        2: [{
            'addr': '192.168.1.2',
            'netmask': '255.255.255.0'
        }]
    }
    
    interfaces = network_mapper.get_network_interfaces()
    assert len(interfaces) == 1
    assert interfaces[0]['name'] == 'eth0'
    assert interfaces[0]['ip'] == '192.168.1.2'
    assert interfaces[0]['netmask'] == '255.255.255.0'

@patch('wifi_fortress.core.network_mapper.NetworkMapper._validate_interface')
@patch('wifi_fortress.core.network_mapper.NetworkMapper._validate_network')
@patch('scapy.all.srp')
def test_scan_network(mock_srp, mock_validate_network, mock_validate_interface, network_mapper):
    # Setup mocks
    mock_validate_interface.return_value = True
    mock_validate_network.return_value = True
    mock_response = Mock()
    mock_response.psrc = '192.168.1.1'
    mock_response.hwsrc = '00:11:22:33:44:55'
    mock_srp.return_value = ([(None, mock_response)], None)
    
    devices = network_mapper.scan_network('eth0', '192.168.1.0/24')
    assert len(devices) == 1
    assert devices[0].ip_address == '192.168.1.1'
    # MAC address will be encrypted
    network_mapper._decrypt_device_data(devices[0])
    assert devices[0].mac_address == '00:11:22:33:44:55'

def test_scan_validation(network_mapper):
    """Test input validation for scanning"""
    with pytest.raises(ValueError):
        network_mapper.scan_network('invalid_interface', '192.168.1.0/24')
        
    with pytest.raises(ValueError):
        network_mapper.scan_network('eth0', 'invalid_network')
        
    with pytest.raises(ValueError):
        network_mapper.scan_network('eth0', '192.168.1.0/16')  # Too large

@patch('wifi_fortress.core.network_mapper.NetworkMapper._validate_interface')
@patch('wifi_fortress.core.network_mapper.NetworkMapper._validate_network')
def test_continuous_scanning_start_stop(mock_validate_network, mock_validate_interface, network_mapper):
    mock_validate_interface.return_value = True
    mock_validate_network.return_value = True
    
    with patch.object(network_mapper, 'scan_network') as mock_scan:
        # Start scanning
        network_mapper.start_continuous_scanning('eth0', '192.168.1.0/24', interval=60)
        assert network_mapper._active_thread is not None
        assert network_mapper._active_thread.is_alive()
        
        # Stop scanning with proper timeout
        assert network_mapper.stop_continuous_scanning(timeout=5)
        
        # Verify thread has stopped
        max_wait = 5  # Maximum time to wait for thread to stop
        start_time = time.time()
        while network_mapper._active_thread.is_alive():
            if time.time() - start_time > max_wait:
                pytest.fail('Thread failed to stop within timeout')
            time.sleep(0.1)
        
        assert not network_mapper._active_thread.is_alive()
        
    # Test validation
    with pytest.raises(ValueError):
        network_mapper.start_continuous_scanning('eth0', '192.168.1.0/24', interval=30)  # Too short
        
    # Test already running case
    network_mapper.start_continuous_scanning('eth0', '192.168.1.0/24')
    with pytest.raises(RuntimeError):
        network_mapper.start_continuous_scanning('eth0', '192.168.1.0/24')  # Already running
    
    # Cleanup
    network_mapper.stop_continuous_scanning(timeout=5)

def test_device_tracking(network_mapper, mock_network_device):
    # Add device with encryption
    network_mapper._encrypt_device_data(mock_network_device)
    network_mapper._devices[mock_network_device.ip_address] = mock_network_device
    
    # Test active devices
    active_devices = network_mapper.get_active_devices()
    assert len(active_devices) == 1
    assert active_devices[0].ip_address == mock_network_device.ip_address
    network_mapper._decrypt_device_data(active_devices[0])
    assert active_devices[0].mac_address == '00:11:22:33:44:55'
    
    # Test device history
    device_history = network_mapper.get_device_history()
    assert len(device_history) == 1
    assert device_history[0].ip_address == mock_network_device.ip_address

def test_error_handling(network_mapper):
    # Test interface error handling
    with patch('netifaces.interfaces', side_effect=Exception('Test error')):
        interfaces = network_mapper.get_network_interfaces()
        assert interfaces == []
    
    # Test scan error handling
    with patch('scapy.all.srp', side_effect=Exception('Test error')):
        with patch.object(network_mapper, '_validate_interface', return_value=True):
            with patch.object(network_mapper, '_validate_network', return_value=True):
                devices = network_mapper.scan_network('eth0', '192.168.1.0/24')
                assert devices == []
    
    # Test timeout handling
    with patch('scapy.all.srp', side_effect=TimeoutError('Scan timeout')):
        with patch.object(network_mapper, '_validate_interface', return_value=True):
            with patch.object(network_mapper, '_validate_network', return_value=True):
                devices = network_mapper.scan_network('eth0', '192.168.1.0/24')
                assert devices == []

def test_rate_limiting(network_mapper):
    """Test rate limiting functionality"""
    with patch.object(network_mapper, '_validate_interface', return_value=True):
        with patch.object(network_mapper, '_validate_network', return_value=True):
            with patch('scapy.all.srp', return_value=([], None)):
                # Reset rate limiter to ensure clean state
                network_mapper._rate_limiter.reset()
                
                # Should allow initial requests
                for i in range(5):
                    try:
                        network_mapper.scan_network('eth0', '192.168.1.0/24')
                    except RuntimeError as e:
                        if 'Rate limit exceeded' in str(e):
                            pytest.fail(f'Rate limit hit too early at request {i}')
                        raise
                
                # Should block additional requests
                with pytest.raises(RuntimeError, match='Rate limit exceeded'):
                    network_mapper.scan_network('eth0', '192.168.1.0/24')
                    
                # Wait for rate limit window to expire and verify we can scan again
                time.sleep(61)  # Wait just over the 60-second window
                try:
                    network_mapper.scan_network('eth0', '192.168.1.0/24')
                except RuntimeError as e:
                    if 'Rate limit exceeded' in str(e):
                        pytest.fail('Rate limit still active after window expiry')
                    raise
