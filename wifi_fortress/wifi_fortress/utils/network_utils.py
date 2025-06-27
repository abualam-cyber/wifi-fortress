import netifaces
import psutil
import subprocess
from typing import List, Dict, Optional
import platform
import re

def get_network_interfaces() -> List[Dict]:
    """Get all network interfaces with their details"""
    interfaces = []
    for iface in netifaces.interfaces():
        try:
            addrs = netifaces.ifaddresses(iface)
            # Get IPv4 info if available
            ipv4 = addrs.get(netifaces.AF_INET, [{}])[0]
            # Get MAC address if available
            mac = addrs.get(netifaces.AF_LINK, [{}])[0].get('addr')
            
            interface_info = {
                'name': iface,
                'ip': ipv4.get('addr', ''),
                'netmask': ipv4.get('netmask', ''),
                'mac': mac or '',
                'is_up': is_interface_up(iface)
            }
            interfaces.append(interface_info)
        except Exception as e:
            print(f"Error getting interface {iface} info: {str(e)}")
    return interfaces

def is_interface_up(interface: str) -> bool:
    """Check if a network interface is up"""
    try:
        addrs = netifaces.ifaddresses(interface)
        return netifaces.AF_INET in addrs
    except Exception:
        return False

def get_wifi_signal_strength(interface: str) -> Optional[int]:
    """Get WiFi signal strength for an interface"""
    if platform.system() == 'Windows':
        try:
            output = subprocess.check_output(
                ['netsh', 'wlan', 'show', 'interfaces'],
                universal_newlines=True
            )
            for line in output.split('\n'):
                if 'Signal' in line and interface in output:
                    match = re.search(r'(\d+)%', line)
                    if match:
                        return int(match.group(1))
        except Exception as e:
            print(f"Error getting signal strength: {str(e)}")
    else:
        try:
            output = subprocess.check_output(
                ['iwconfig', interface],
                universal_newlines=True,
                stderr=subprocess.DEVNULL
            )
            match = re.search(r'Signal level=(-\d+)', output)
            if match:
                # Convert dBm to percentage (rough approximation)
                dbm = int(match.group(1))
                # Signal strength usually ranges from -100 dBm (0%) to -50 dBm (100%)
                percentage = max(0, min(100, 2 * (dbm + 100)))
                return percentage
        except Exception as e:
            print(f"Error getting signal strength: {str(e)}")
    return None

def get_network_usage(interface: str) -> Dict[str, float]:
    """Get network usage statistics for an interface"""
    try:
        stats = psutil.net_io_counters(pernic=True).get(interface)
        if stats:
            return {
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv,
                'errin': stats.errin,
                'errout': stats.errout,
                'dropin': stats.dropin,
                'dropout': stats.dropout
            }
    except Exception as e:
        print(f"Error getting network usage: {str(e)}")
    return {
        'bytes_sent': 0,
        'bytes_recv': 0,
        'packets_sent': 0,
        'packets_recv': 0,
        'errin': 0,
        'errout': 0,
        'dropin': 0,
        'dropout': 0
    }

def format_bytes(bytes: float) -> str:
    """Format bytes into human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} PB"
