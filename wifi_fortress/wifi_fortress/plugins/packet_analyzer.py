from wifi_fortress.core.plugin_loader import Plugin
import scapy.all as scapy
from threading import Thread
from typing import Dict, List, Set
import time
from datetime import datetime
import json
from cryptography.fernet import Fernet
import os

class PacketAnalyzer(Plugin):
    name = 'Packet Analyzer'
    description = 'Analyzes network traffic for security threats'
    version = '1.0.0'
    author = 'WiFi Fortress Team'
    
    def __init__(self):
        super().__init__()
        self.analyzer_thread = None
        self.suspicious_ips: Set[str] = set()
        self.packet_stats: Dict[str, Dict] = {}
        self.attack_patterns = {
            'deauth': 0,
            'beacon_flood': 0,
            'arp_spoof': 0
        }
        self.log_file = 'packet_analysis.log'
        self.encryption_key = None
        
    def initialize(self) -> bool:
        """Initialize the packet analyzer"""
        try:
            # Generate or load encryption key for secure logging
            key_file = 'analysis.key'
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
            else:
                self.encryption_key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(self.encryption_key)
            
            self.cipher_suite = Fernet(self.encryption_key)
            return True
        except Exception as e:
            print(f"Failed to initialize packet analyzer: {str(e)}")
            return False
    
    def start_analysis(self):
        """Start packet analysis"""
        if not self.enabled:
            return
            
        def analyze_worker():
            while self.enabled:
                try:
                    # Sniff packets
                    packets = scapy.sniff(count=100, timeout=5)
                    self.analyze_packets(packets)
                except Exception as e:
                    print(f"Error in packet analysis: {str(e)}")
                    time.sleep(5)
                    
        self.analyzer_thread = Thread(target=analyze_worker)
        self.analyzer_thread.daemon = True
        self.analyzer_thread.start()
        
    def analyze_packets(self, packets: List[scapy.Packet]):
        """Analyze captured packets for security threats"""
        for packet in packets:
            try:
                # Check for deauthentication attacks
                if packet.haslayer(scapy.Dot11Deauth):
                    self.attack_patterns['deauth'] += 1
                    self.log_security_event('Potential deauthentication attack detected')
                
                # Check for beacon frame flooding
                elif packet.haslayer(scapy.Dot11Beacon):
                    if self.detect_beacon_flood(packet):
                        self.attack_patterns['beacon_flood'] += 1
                        self.log_security_event('Potential beacon flooding attack detected')
                
                # Check for ARP spoofing
                elif packet.haslayer(scapy.ARP):
                    if self.detect_arp_spoof(packet):
                        self.attack_patterns['arp_spoof'] += 1
                        self.log_security_event('Potential ARP spoofing attack detected')
                
                # Update packet statistics
                self.update_packet_stats(packet)
                
            except Exception as e:
                print(f"Error analyzing packet: {str(e)}")
    
    def detect_beacon_flood(self, packet: scapy.Packet) -> bool:
        """Detect beacon frame flooding attacks"""
        try:
            ssid = packet[scapy.Dot11Elt].info.decode()
            bssid = packet[scapy.Dot11].addr3
            
            # Check for suspicious number of different SSIDs from same BSSID
            if bssid not in self.packet_stats:
                self.packet_stats[bssid] = {'ssids': set(), 'last_seen': time.time()}
            
            self.packet_stats[bssid]['ssids'].add(ssid)
            
            # If more than 10 different SSIDs from same BSSID in short time, flag as suspicious
            if len(self.packet_stats[bssid]['ssids']) > 10:
                return True
        except Exception:
            pass
        return False
    
    def detect_arp_spoof(self, packet: scapy.Packet) -> bool:
        """Detect ARP spoofing attacks"""
        if packet[scapy.ARP].op == 2:  # ARP Reply
            try:
                real_mac = scapy.getmacbyip(packet[scapy.ARP].psrc)
                response_mac = packet[scapy.ARP].hwsrc
                
                if real_mac and real_mac != response_mac:
                    self.suspicious_ips.add(packet[scapy.ARP].psrc)
                    return True
            except Exception:
                pass
        return False
    
    def update_packet_stats(self, packet: scapy.Packet):
        """Update packet statistics"""
        timestamp = time.time()
        
        # Clean old entries
        for addr in list(self.packet_stats.keys()):
            if timestamp - self.packet_stats[addr]['last_seen'] > 300:  # 5 minutes
                del self.packet_stats[addr]
    
    def log_security_event(self, event: str):
        """Log security events with encryption"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = {
                'timestamp': timestamp,
                'event': event,
                'attack_patterns': self.attack_patterns.copy(),
                'suspicious_ips': list(self.suspicious_ips)
            }
            
            # Encrypt the log entry
            encrypted_data = self.cipher_suite.encrypt(
                json.dumps(log_entry).encode()
            )
            
            # Write encrypted log
            with open(self.log_file, 'ab') as f:
                f.write(encrypted_data + b'\n')
                
            print(f"Security Event: {event}")
        except Exception as e:
            print(f"Error logging security event: {str(e)}")
    
    def cleanup(self) -> bool:
        """Stop analysis and cleanup"""
        self.enabled = False
        if self.analyzer_thread:
            self.analyzer_thread.join(timeout=2)
        return True
