import logging
import ipaddress
import threading
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from cryptography.fernet import Fernet
from pathlib import Path

from scapy.all import ARP, Ether, srp
import netifaces

from .rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NetworkDevice:
    """Represents a device discovered on the network"""
    ip_address: str
    mac_address: str
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    first_seen: datetime = datetime.now()
    last_seen: datetime = datetime.now()
    is_active: bool = True

class NetworkMapper:
    """Core network mapping functionality for WiFi Fortress with enhanced security"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize NetworkMapper with optional encryption
        
        Args:
            encryption_key: Optional encryption key for sensitive data
        """
        self._devices: Dict[str, NetworkDevice] = {}
        self._lock = threading.Lock()
        self._stop_scan = threading.Event()
        self._active_thread: Optional[threading.Thread] = None
        self._last_scan_time: Dict[str, datetime] = {}
        
        # Rate limiting
        self._rate_limiter = RateLimiter(max_requests=5, time_window=60)  # 5 scans per minute
        
        # Encryption setup
        if encryption_key:
            self._fernet = Fernet(encryption_key.encode())
        else:
            self._fernet = None
            
        # Validation constraints
        self._max_concurrent_scans = 3
        self._active_scans = 0
        self._scan_timeout = 30  # seconds
        
    def get_network_interfaces(self) -> List[Dict]:
        """Get list of available network interfaces"""
        try:
            interfaces = []
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:  # Has IPv4
                    interfaces.append({
                        'name': iface,
                        'ip': addrs[netifaces.AF_INET][0]['addr'],
                        'netmask': addrs[netifaces.AF_INET][0]['netmask']
                    })
            return interfaces
        except Exception as e:
            logger.error(f'Error getting network interfaces: {str(e)}')
            return []

    def _validate_network(self, network: str) -> bool:
        """Validate network address format and range"""
        try:
            net = ipaddress.ip_network(network)
            # Prevent scanning large networks
            if net.num_addresses > 256:
                logger.error(f'Network too large: {net.num_addresses} addresses')
                return False
            return True
        except ValueError as e:
            logger.error(f'Invalid network address: {str(e)}')
            return False
    
    def _validate_interface(self, interface: str) -> bool:
        """Validate network interface exists"""
        try:
            return interface in netifaces.interfaces()
        except Exception as e:
            logger.error(f'Error validating interface: {str(e)}')
            return False
    
    def _encrypt_device_data(self, device: NetworkDevice) -> None:
        """Encrypt sensitive device data if encryption is enabled"""
        if self._fernet:
            device.mac_address = self._fernet.encrypt(device.mac_address.encode()).decode()
            if device.hostname:
                device.hostname = self._fernet.encrypt(device.hostname.encode()).decode()
    
    def _decrypt_device_data(self, device: NetworkDevice) -> None:
        """Decrypt device data if encryption is enabled"""
        if self._fernet:
            device.mac_address = self._fernet.decrypt(device.mac_address.encode()).decode()
            if device.hostname:
                device.hostname = self._fernet.decrypt(device.hostname.encode()).decode()
    
    def scan_network(self, interface: str, network: str) -> List[NetworkDevice]:
        """
        Perform a network scan with input validation and rate limiting
        
        Args:
            interface: Network interface to use
            network: Network address in CIDR notation (e.g., '192.168.1.0/24')
            
        Returns:
            List of discovered NetworkDevice objects
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If rate limit exceeded
        """
        # Input validation
        if not self._validate_interface(interface):
            raise ValueError(f'Invalid interface: {interface}')
        if not self._validate_network(network):
            raise ValueError(f'Invalid network: {network}')
            
        # Rate limiting
        if not self._rate_limiter.allow_request():
            raise RuntimeError('Rate limit exceeded. Please wait before scanning again.')
            
        # Concurrency control
        with self._lock:
            if self._active_scans >= self._max_concurrent_scans:
                raise RuntimeError('Maximum concurrent scans reached')
            self._active_scans += 1
            
        try:
            logger.info(f'Starting network scan on {interface} for network {network}')
            
            # Create ARP request packet
            net = ipaddress.ip_network(network)
            arp = ARP(pdst=str(net))
            ether = Ether(dst='ff:ff:ff:ff:ff:ff')
            packet = ether/arp

            # Send packet and get response with timeout
            start_time = time.time()
            try:
                result = srp(packet, timeout=min(3, self._scan_timeout), iface=interface, verbose=False)[0]
            except TimeoutError:
                logger.warning(f'Scan timeout on {interface} for network {network}')
                return []
            except Exception as e:
                logger.error(f'Error during ARP scan: {str(e)}')
                return []
            
            if time.time() - start_time > self._scan_timeout:
                logger.warning(f'Scan timeout exceeded on {interface}')
                return []
            
            devices = []
            try:
                for sent, received in result:
                    try:
                        device = NetworkDevice(
                            ip_address=received.psrc,
                            mac_address=received.hwsrc
                        )
                        # Encrypt sensitive data
                        self._encrypt_device_data(device)
                        devices.append(device)
                        
                        with self._lock:
                            if device.ip_address not in self._devices:
                                self._devices[device.ip_address] = device
                            else:
                                self._devices[device.ip_address].last_seen = datetime.now()
                                self._devices[device.ip_address].is_active = True
                    except Exception as e:
                        logger.error(f'Error processing device response: {str(e)}')
                        continue
            except Exception as e:
                logger.error(f'Error processing scan results: {str(e)}')
                return devices  # Return any devices we managed to process
            
            logger.info(f'Discovered {len(devices)} devices on network {network}')
            return devices
            
        except Exception as e:
            logger.error(f'Unhandled error during network scan: {str(e)}')
            return []
        finally:
            with self._lock:
                self._active_scans -= 1

    def start_continuous_scanning(self, interface: str, network: str, interval: int = 300):
        """
        Start continuous network scanning in background with safety checks
        
        Args:
            interface: Network interface to use
            network: Network address in CIDR notation
            interval: Scan interval in seconds (default: 300)
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If scanning already active
        """
        # Validate inputs before starting thread
        if not self._validate_interface(interface):
            raise ValueError(f'Invalid interface: {interface}')
        if not self._validate_network(network):
            raise ValueError(f'Invalid network: {network}')
        if interval < 60:  # Minimum 1 minute interval
            raise ValueError('Interval must be at least 60 seconds')
            
        if self._active_thread and self._active_thread.is_alive():
            raise RuntimeError('Continuous scanning already running')
            
        def _scan_loop():
            while not self._stop_scan.is_set():
                try:
                    self.scan_network(interface, network)
                except Exception as e:
                    logger.error(f'Error in continuous scan: {str(e)}')
                    if isinstance(e, RuntimeError) and 'Rate limit exceeded' in str(e):
                        # Wait for rate limit to reset
                        time.sleep(60)
                finally:
                    # Use event with timeout to allow clean shutdown
                    self._stop_scan.wait(interval)

        self._stop_scan.clear()
        self._active_thread = threading.Thread(target=_scan_loop, name='continuous_scan')
        self._active_thread.daemon = True
        self._active_thread.start()
        logger.info(f'Started continuous scanning on {interface} every {interval} seconds')

    def stop_continuous_scanning(self, timeout: int = 10) -> bool:
        """Stop continuous network scanning with timeout
        
        Args:
            timeout: Maximum time to wait for thread completion in seconds
            
        Returns:
            bool: True if scanning was stopped successfully
        """
        if self._active_thread and self._active_thread.is_alive():
            self._stop_scan.set()
            try:
                self._active_thread.join(timeout=timeout)
                if self._active_thread.is_alive():
                    logger.error('Failed to stop scanning thread within timeout')
                    return False
                logger.info('Stopped continuous scanning')
                return True
            except Exception as e:
                logger.error(f'Error stopping continuous scan: {str(e)}')
                return False
        return True  # No active thread to stop

    def get_active_devices(self) -> List[NetworkDevice]:
        """Get list of currently active devices"""
        with self._lock:
            return [device for device in self._devices.values() if device.is_active]

    def get_device_history(self) -> List[NetworkDevice]:
        """Get historical list of all discovered devices"""
        with self._lock:
            return list(self._devices.values())