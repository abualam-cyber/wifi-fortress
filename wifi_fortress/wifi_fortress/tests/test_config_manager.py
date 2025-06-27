import os
import json
import pytest
from pathlib import Path
from wifi_fortress.core.config_manager import ConfigManager

@pytest.fixture
def temp_config_dir(tmp_path):
    return str(tmp_path / 'test_config')

@pytest.fixture
def config_manager(temp_config_dir):
    return ConfigManager(config_dir=temp_config_dir)

def test_config_creation(temp_config_dir):
    """Test that config file is created with defaults"""
    cm = ConfigManager(config_dir=temp_config_dir)
    config_file = Path(temp_config_dir) / 'config.json'
    
    assert config_file.exists()
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    assert 'logging' in config
    assert 'network_scanner' in config
    assert 'security' in config
    assert 'plugins' in config

def test_get_config_value(config_manager):
    """Test getting config values"""
    assert config_manager.get('logging.level') == 'INFO'
    assert config_manager.get('network_scanner.scan_interval') == 300
    assert config_manager.get('nonexistent.key', 'default') == 'default'

def test_set_config_value(config_manager):
    """Test setting config values"""
    assert config_manager.set('logging.level', 'DEBUG')
    assert config_manager.get('logging.level') == 'DEBUG'
    
    assert config_manager.set('new.key', 'value')
    assert config_manager.get('new.key') == 'value'

def test_reset_config(config_manager):
    """Test resetting config to defaults"""
    config_manager.set('logging.level', 'DEBUG')
    assert config_manager.reset()
    assert config_manager.get('logging.level') == 'INFO'
