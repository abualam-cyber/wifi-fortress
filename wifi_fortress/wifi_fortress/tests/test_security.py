"""Tests for security module"""

import os
import hashlib
import pytest
from pathlib import Path
from cryptography.fernet import Fernet

from wifi_fortress.core.security import SecurityManager, SecurityError
from wifi_fortress.core.error_handler import handle_errors

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory"""
    config_dir = tmp_path / 'config'
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def security_manager(temp_config_dir):
    """Create security manager instance"""
    return SecurityManager(temp_config_dir)

def test_encryption(security_manager):
    """Test data encryption/decryption"""
    # Test string encryption
    test_str = "sensitive data"
    encrypted = security_manager.encrypt_data(test_str)
    decrypted = security_manager.decrypt_data(encrypted)
    assert decrypted == test_str
    
    # Test dict encryption
    test_dict = {"key": "value", "number": 123}
    encrypted = security_manager.encrypt_data(test_dict)
    decrypted = security_manager.decrypt_data(encrypted)
    assert decrypted == test_dict

def test_plugin_validation(security_manager, tmp_path):
    """Test plugin validation"""
    # Create test plugin file
    plugin_dir = tmp_path / 'plugins'
    plugin_dir.mkdir()
    
    # Valid plugin
    valid_plugin = plugin_dir / 'valid_plugin.py'
    valid_plugin.write_text('''
from wifi_fortress.core.plugin_loader import Plugin

class TestPlugin(Plugin):
    name = "Test Plugin"
    description = "Test plugin for validation"
    version = "1.0.0"
    author = "Test Author"
    
    def initialize(self) -> bool:
        return True
        
    def cleanup(self) -> bool:
        return True
''')
    
    # Invalid plugin with dangerous imports
    invalid_plugin = plugin_dir / 'invalid_plugin.py'
    invalid_plugin.write_text('''
import os
import subprocess

def dangerous_function():
    os.system('rm -rf /')
    subprocess.run(['format', 'c:'])
''')
    
    # Test validation
    assert security_manager.validate_plugin(valid_plugin) is True
    
    with pytest.raises(SecurityError, match='Plugin contains potentially dangerous code'):
        security_manager.validate_plugin(invalid_plugin)

def test_input_sanitization(security_manager):
    """Test input sanitization"""
    # Test string sanitization
    dangerous_input = '<script>alert("xss");</script>'
    safe_input = security_manager.sanitize_input(dangerous_input)
    assert '<script>' not in safe_input
    assert 'script' in safe_input
    
    # Test dict sanitization
    dangerous_dict = {
        'cmd': 'ls; rm -rf /',
        'input': '<img src="x" onerror="alert(1)">',
        'nested': {
            'danger': '`cat /etc/passwd`'
        }
    }
    safe_dict = security_manager.sanitize_input(dangerous_dict)
    assert ';' not in safe_dict['cmd']
    assert '<img' not in safe_dict['input']
    assert '`' not in safe_dict['nested']['danger']

def test_signature_verification(security_manager):
    """Test digital signature verification"""
    # Create test data and key
    data = b'test data'
    key = os.urandom(32)
    
    # Create valid signature
    import hmac
    import hashlib
    valid_sig = hmac.new(key, data, hashlib.sha256).digest()
    
    # Create invalid signature
    invalid_sig = os.urandom(32)
    
    # Test verification
    assert security_manager.verify_signature(data, valid_sig, key)
    assert not security_manager.verify_signature(data, invalid_sig, key)

def test_key_persistence(temp_config_dir):
    """Test encryption key persistence"""
    # Create first instance
    sm1 = SecurityManager(temp_config_dir)
    test_data = "test data"
    encrypted = sm1.encrypt_data(test_data)
    
    # Create second instance
    sm2 = SecurityManager(temp_config_dir)
    decrypted = sm2.decrypt_data(encrypted)
    
    assert decrypted == test_data

def test_error_handling(security_manager):
    """Test security error handling"""
    # Test invalid data decryption
    with pytest.raises(SecurityError, match='Failed to decrypt data'):
        security_manager.decrypt_data(b'invalid data')
    
    # Test non-existent plugin validation
    with pytest.raises(SecurityError, match='Plugin file not found'):
        security_manager.validate_plugin(Path('non_existent.py'))
    
    # Test invalid signature verification
    with pytest.raises(SecurityError, match='Signature verification failed'):
        security_manager.verify_signature(None, None, None)

def test_plugin_hash_lists(security_manager, tmp_path):
    """Test plugin hash whitelisting and blacklisting"""
    # Create test plugin file
    plugin_dir = tmp_path / 'plugins'
    plugin_dir.mkdir()
    
    # Create a test plugin
    test_plugin = plugin_dir / 'test_plugin.py'
    test_plugin.write_text('''
from wifi_fortress.core.plugin_loader import Plugin

class TestPlugin(Plugin):
    name = "Test Plugin"
    description = "Test plugin for validation"
    version = "1.0.0"
    author = "Test Author"
    
    def initialize(self) -> bool:
        return True
        
    def cleanup(self) -> bool:
        return True
''')
    
    # Calculate plugin hash
    with open(test_plugin, 'rb') as f:
        content = f.read()
    plugin_hash = hashlib.sha256(content).hexdigest()
    
    # Test whitelisting first
    security_manager.add_to_whitelist(plugin_hash)
    assert security_manager.validate_plugin(test_plugin) is True
    
    # Test blacklisting
    security_manager.add_to_blacklist(plugin_hash)
    with pytest.raises(SecurityError, match='Plugin hash .* is blacklisted'):
        security_manager.validate_plugin(test_plugin)
