import pytest
import os
import tempfile
from wifi_fortress.core.secure_config import SecureConfigManager

@pytest.fixture
def config_file():
    """Create temporary config file"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def secure_config(config_file):
    """Create SecureConfigManager instance"""
    return SecureConfigManager(config_file, 'test_password')

def test_secure_config_init(secure_config):
    """Test secure config initialization"""
    assert secure_config._config == {}
    assert secure_config._fernet is not None

def test_save_and_load_config(secure_config):
    """Test saving and loading encrypted config"""
    # Set some test values
    secure_config.set_value('test_key', 'test_value')
    secure_config.set_value('nested.key', 'nested_value')
    
    # Save config
    assert secure_config.save_config()
    
    # Create new instance with same password
    new_config = SecureConfigManager(secure_config.config_path, 'test_password')
    assert new_config.load_config()
    
    # Check values
    assert new_config.get_value('test_key') == 'test_value'
    assert new_config.get_value('nested.key') == 'nested_value'

def test_wrong_password(config_file):
    """Test loading with wrong password"""
    # Save config with one password
    config1 = SecureConfigManager(config_file, 'password1')
    config1.set_value('key', 'value')
    assert config1.save_config()
    
    # Try to load with different password
    config2 = SecureConfigManager(config_file, 'password2')
    assert not config2.load_config()

def test_nested_config(secure_config):
    """Test nested configuration values"""
    secure_config.set_value('level1.level2.level3', 'deep_value')
    assert secure_config.get_value('level1.level2.level3') == 'deep_value'
    
    # Get intermediate level
    level2 = secure_config.get_value('level1.level2')
    assert isinstance(level2, dict)
    assert level2['level3'] == 'deep_value'

def test_delete_value(secure_config):
    """Test deleting configuration values"""
    secure_config.set_value('test_key', 'test_value')
    assert secure_config.get_value('test_key') == 'test_value'
    
    assert secure_config.delete_value('test_key')
    assert secure_config.get_value('test_key') is None
    
    # Test deleting nested value
    secure_config.set_value('nested.key', 'value')
    assert secure_config.delete_value('nested.key')
    assert secure_config.get_value('nested.key') is None

def test_reset_config(secure_config):
    """Test resetting configuration"""
    secure_config.set_value('key1', 'value1')
    secure_config.set_value('key2', 'value2')
    
    assert secure_config.reset_config()
    assert secure_config.get_all_config() == {}

def test_change_master_password(secure_config):
    """Test changing master password"""
    # Set initial values
    secure_config.set_value('key', 'value')
    assert secure_config.save_config()
    
    # Change password
    assert secure_config.change_master_password('new_password')
    
    # Try to load with new password
    new_config = SecureConfigManager(secure_config.config_path, 'new_password')
    assert new_config.load_config()
    assert new_config.get_value('key') == 'value'
    
    # Try to load with old password should fail
    old_config = SecureConfigManager(secure_config.config_path, 'test_password')
    assert not old_config.load_config()

def test_default_values(secure_config):
    """Test default value handling"""
    assert secure_config.get_value('nonexistent') is None
    assert secure_config.get_value('nonexistent', 'default') == 'default'
    
    # Test nested default
    assert secure_config.get_value('nested.nonexistent', 42) == 42

def test_invalid_operations(secure_config):
    """Test handling of invalid operations"""
    # Try to get value with invalid key type
    with pytest.raises(Exception):
        secure_config.get_value(None)
    
    # Try to set value with invalid key
    with pytest.raises(Exception):
        secure_config.set_value(None, 'value')
