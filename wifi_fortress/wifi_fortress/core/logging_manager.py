import logging
import logging.handlers
import os
import json
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime

class LoggingManager:
    """Centralized logging management for WiFi Fortress"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(Path.home() / '.wifi_fortress' / 'logging.json')
        self.default_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                },
                'simple': {
                    'format': '%(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'simple',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'detailed',
                    'filename': str(Path.home() / '.wifi_fortress' / 'logs' / 'wifi_fortress.log'),
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                },
                'security': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'INFO',
                    'formatter': 'detailed',
                    'filename': str(Path.home() / '.wifi_fortress' / 'logs' / 'security.log'),
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 10
                },
                'error': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'ERROR',
                    'formatter': 'detailed',
                    'filename': str(Path.home() / '.wifi_fortress' / 'logs' / 'error.log'),
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 10
                }
            },
            'loggers': {
                'wifi_fortress': {
                    'level': 'DEBUG',
                    'handlers': ['console', 'file'],
                    'propagate': False
                },
                'wifi_fortress.security': {
                    'level': 'INFO',
                    'handlers': ['security', 'console'],
                    'propagate': False
                },
                'wifi_fortress.error': {
                    'level': 'ERROR',
                    'handlers': ['error', 'console'],
                    'propagate': False
                }
            }
        }
        
    def setup_logging(self) -> bool:
        """Setup logging configuration
        
        Returns:
            bool: True if setup successful
        """
        try:
            config = self._load_config()
            
            # Create log directory if it doesn't exist
            log_dir = Path.home() / '.wifi_fortress' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure logging
            logging.config.dictConfig(config)
            
            # Log startup
            logger = logging.getLogger('wifi_fortress')
            logger.info('Logging system initialized')
            return True
            
        except Exception as e:
            print(f'Error setting up logging: {e}')
            return False
            
    def _load_config(self) -> Dict:
        """Load logging configuration
        
        Returns:
            Dict: Logging configuration
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f'Error loading logging config: {e}')
                
        return self.default_config
        
    def save_config(self, config: Dict) -> bool:
        """Save logging configuration
        
        Args:
            config: Logging configuration to save
            
        Returns:
            bool: True if save successful
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f'Error saving logging config: {e}')
            return False
            
    def get_logger(self, name: str) -> logging.Logger:
        """Get logger by name
        
        Args:
            name: Logger name
            
        Returns:
            logging.Logger: Logger instance
        """
        return logging.getLogger(f'wifi_fortress.{name}')
        
    def set_log_level(self, name: str, level: str) -> bool:
        """Set log level for a logger
        
        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            bool: True if level was set
        """
        try:
            logger = logging.getLogger(f'wifi_fortress.{name}')
            logger.setLevel(getattr(logging, level.upper()))
            return True
        except Exception as e:
            print(f'Error setting log level: {e}')
            return False
            
    def add_file_handler(self, name: str, filename: str,
                        level: str = 'INFO', max_bytes: int = 10485760,
                        backup_count: int = 5) -> bool:
        """Add a new file handler to a logger
        
        Args:
            name: Logger name
            filename: Log file name
            level: Log level
            max_bytes: Maximum file size in bytes
            backup_count: Number of backup files to keep
            
        Returns:
            bool: True if handler was added
        """
        try:
            logger = logging.getLogger(f'wifi_fortress.{name}')
            
            # Create handler
            handler = logging.handlers.RotatingFileHandler(
                filename=filename,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            
            # Set level and formatter
            handler.setLevel(getattr(logging, level.upper()))
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            # Add handler
            logger.addHandler(handler)
            return True
        except Exception as e:
            print(f'Error adding file handler: {e}')
            return False
            
    def rotate_logs(self) -> bool:
        """Rotate all log files
        
        Returns:
            bool: True if rotation successful
        """
        try:
            for handler in logging.getLogger('wifi_fortress').handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.doRollover()
            return True
        except Exception as e:
            print(f'Error rotating logs: {e}')
            return False
