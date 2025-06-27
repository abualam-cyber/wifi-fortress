from wifi_fortress.core.plugin_loader import Plugin
import subprocess
import platform
import re
from typing import List, Dict
import json
import os
from threading import Thread
import time

class FirewallManager(Plugin):
    name = 'Firewall Manager'
    description = 'Manages firewall rules and security policies'
    version = '1.0.0'
    author = 'WiFi Fortress Team'
    
    def __init__(self):
        super().__init__()
        self.os_type = platform.system().lower()
        self.monitor_thread = None
        self.rules: List[Dict] = []
        self.blocked_ips: set = set()
        self.config_file = 'firewall_config.json'
        
    def initialize(self) -> bool:
        """Initialize the firewall manager"""
        try:
            # Load existing configuration
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.rules = config.get('rules', [])
                    self.blocked_ips = set(config.get('blocked_ips', []))
            
            # Verify firewall access
            if self.os_type == 'windows':
                subprocess.run(['netsh', 'advfirewall', 'show', 'currentprofile'],
                             check=True, capture_output=True)
            else:
                subprocess.run(['sudo', 'iptables', '-L'],
                             check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"Failed to initialize firewall manager: {str(e)}")
            return False
    
    def start_monitoring(self):
        """Start firewall monitoring"""
        if not self.enabled:
            return
            
        def monitor_worker():
            while self.enabled:
                try:
                    self.check_firewall_status()
                    self.update_rules()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    print(f"Error in firewall monitoring: {str(e)}")
                    time.sleep(300)  # Wait 5 minutes on error
                    
        self.monitor_thread = Thread(target=monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def check_firewall_status(self) -> Dict:
        """Check firewall status and active rules"""
        status = {'enabled': False, 'active_rules': 0}
        
        try:
            if self.os_type == 'windows':
                output = subprocess.check_output(
                    ['netsh', 'advfirewall', 'show', 'allprofiles'],
                    universal_newlines=True
                )
                status['enabled'] = 'ON' in output
                
                # Count active rules
                rule_output = subprocess.check_output(
                    ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
                    universal_newlines=True
                )
                status['active_rules'] = len(re.findall(r'Rule Name:', rule_output))
                
            else:  # Linux
                output = subprocess.check_output(
                    ['sudo', 'iptables', '-L'],
                    universal_newlines=True
                )
                status['enabled'] = len(output.strip()) > 0
                status['active_rules'] = len(re.findall(r'^Chain', output, re.M))
                
            print(f"Firewall Status: {json.dumps(status, indent=2)}")
            return status
            
        except Exception as e:
            print(f"Error checking firewall status: {str(e)}")
            return status
    
    def add_rule(self, rule: Dict) -> bool:
        """Add a new firewall rule"""
        try:
            if self.os_type == 'windows':
                cmd = ['netsh', 'advfirewall', 'firewall', 'add', 'rule']
                cmd.extend(['name=' + rule['name']])
                cmd.extend(['dir=' + rule['direction']])
                cmd.extend(['action=' + rule['action']])
                
                if 'port' in rule:
                    cmd.extend(['localport=' + str(rule['port'])])
                if 'protocol' in rule:
                    cmd.extend(['protocol=' + rule['protocol']])
                
                subprocess.run(cmd, check=True)
                
            else:  # Linux
                cmd = ['sudo', 'iptables']
                if rule['action'].lower() == 'block':
                    cmd.extend(['-A', 'INPUT'])
                    cmd.extend(['-j', 'DROP'])
                else:
                    cmd.extend(['-A', 'INPUT'])
                    cmd.extend(['-j', 'ACCEPT'])
                
                if 'port' in rule:
                    cmd.extend(['--dport', str(rule['port'])])
                if 'protocol' in rule:
                    cmd.extend(['-p', rule['protocol']])
                
                subprocess.run(cmd, check=True)
            
            self.rules.append(rule)
            self.save_config()
            return True
            
        except Exception as e:
            print(f"Error adding firewall rule: {str(e)}")
            return False
    
    def block_ip(self, ip: str) -> bool:
        """Block an IP address"""
        try:
            if self.os_type == 'windows':
                cmd = [
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    f'name=Block_{ip}',
                    'dir=in',
                    'action=block',
                    f'remoteip={ip}'
                ]
            else:  # Linux
                cmd = [
                    'sudo', 'iptables',
                    '-A', 'INPUT',
                    '-s', ip,
                    '-j', 'DROP'
                ]
            
            subprocess.run(cmd, check=True)
            self.blocked_ips.add(ip)
            self.save_config()
            print(f"Blocked IP: {ip}")
            return True
            
        except Exception as e:
            print(f"Error blocking IP {ip}: {str(e)}")
            return False
    
    def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address"""
        try:
            if self.os_type == 'windows':
                cmd = [
                    'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                    f'name=Block_{ip}'
                ]
            else:  # Linux
                cmd = [
                    'sudo', 'iptables',
                    '-D', 'INPUT',
                    '-s', ip,
                    '-j', 'DROP'
                ]
            
            subprocess.run(cmd, check=True)
            self.blocked_ips.discard(ip)
            self.save_config()
            print(f"Unblocked IP: {ip}")
            return True
            
        except Exception as e:
            print(f"Error unblocking IP {ip}: {str(e)}")
            return False
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            config = {
                'rules': self.rules,
                'blocked_ips': list(self.blocked_ips)
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving firewall configuration: {str(e)}")
    
    def update_rules(self):
        """Update and verify all firewall rules"""
        for rule in self.rules:
            try:
                # Verify rule exists and is active
                if self.os_type == 'windows':
                    cmd = ['netsh', 'advfirewall', 'firewall', 'show', 'rule',
                          f'name={rule["name"]}']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if 'No rules match the specified criteria' in result.stdout:
                        print(f"Reinstating rule: {rule['name']}")
                        self.add_rule(rule)
            except Exception as e:
                print(f"Error updating rule {rule.get('name', '')}: {str(e)}")
    
    def cleanup(self) -> bool:
        """Stop monitoring and cleanup"""
        self.enabled = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.save_config()
        return True
