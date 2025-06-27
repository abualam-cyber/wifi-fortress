import os
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """Configuration management for WiFi Fortress"""
    
    DEFAULT_CONFIG = {
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'wifi_fortress.log'
        },
        'network_scanner': {
            'scan_interval': 300,  # seconds
            'timeout': 3,  # seconds
            'auto_start': False
        },
        'security': {
            'enable_encryption': True,
            'key_rotation_interval': 86400,  # 24 hours
            'min_password_length': 12
        },
        'plugins': {
            'enabled': [],
            'auto_load': True,
            'plugin_dir': 'plugins'
        }
    }
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.expanduser('~/.wifi_fortress')
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / 'config.json'
        self.config: Dict[str, Any] = {}
        self._load_config()
        
    def _load_config(self) -> None:
        """Load configuration from file or create default"""
        try:
            if not self.config_dir.exists():
                self.config_dir.mkdir(parents=True)
                
            if not self.config_file.exists():
                self.config = self.DEFAULT_CONFIG.copy()
                self._save_config()
            else:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                    
                # Update with any missing default values
                self._update_missing_defaults(self.config, self.DEFAULT_CONFIG)
                
        except Exception as e:
            logger.error(f'Error loading configuration: {str(e)}')
            self.config = self.DEFAULT_CONFIG.copy()
            
    def _save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f'Error saving configuration: {str(e)}')
            return False
            
    def _update_missing_defaults(self, config: Dict, defaults: Dict) -> None:
        """Recursively update config with missing default values"""
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
            elif isinstance(value, dict):
                if not isinstance(config[key], dict):
                    config[key] = value
                else:
                    self._update_missing_defaults(config[key], value)
                    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value by key"""
        try:
            keys = key.split('.')
            config = self.config
            for k in keys[:-1]:
                if k not in config or not isinstance(config[k], dict):
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
            return self._save_config()
        except Exception as e:
            logger.error(f'Error setting configuration {key}: {str(e)}')
            return False
            
    def reset(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self.config = self.DEFAULT_CONFIG.copy()
            return self._save_config()
        except Exception as e:
            logger.error(f'Error resetting configuration: {str(e)}')
            return False
