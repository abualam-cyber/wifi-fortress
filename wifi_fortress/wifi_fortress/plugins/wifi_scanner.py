from wifi_fortress.core.plugin_loader import Plugin
import scapy.all as scapy
from threading import Thread
import time

class WiFiScanner(Plugin):
    name = 'WiFi Scanner'
    description = 'Scans for nearby WiFi networks'
    version = '1.0.0'
    author = 'WiFi Fortress Team'
    
    def __init__(self):
        super().__init__()
        self.networks = []
        self.scan_thread = None
        
    def initialize(self) -> bool:
        """Initialize the WiFi scanner"""
        try:
            # Test if we can use scapy
            scapy.conf.iface
            return True
        except Exception as e:
            print(f'Failed to initialize WiFi scanner: {str(e)}')
            return False
            
    def start_scan(self):
        """Start scanning for networks"""
        if not self.enabled:
            return
            
        def scan_worker():
            while self.enabled:
                try:
                    # Perform network scan
                    packets = scapy.sniff(count=10, timeout=2)
                    for packet in packets:
                        if packet.haslayer(scapy.Dot11Beacon):
                            ssid = packet[scapy.Dot11Elt].info.decode()
                            bssid = packet[scapy.Dot11].addr2
                            channel = int(ord(packet[scapy.Dot11Elt:3].info))
                            
                            network = {
                                'ssid': ssid,
                                'bssid': bssid,
                                'channel': channel
                            }
                            
                            if network not in self.networks:
                                self.networks.append(network)
                                print(f'Found network: {ssid} ({bssid}) on channel {channel}')
                                
                    time.sleep(1)
                except Exception as e:
                    print(f'Error during scan: {str(e)}')
                    time.sleep(5)
                    
        self.scan_thread = Thread(target=scan_worker)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        
    def cleanup(self) -> bool:
        """Stop scanning and cleanup"""
        self.enabled = False
        if self.scan_thread:
            self.scan_thread.join(timeout=2)
        return True
