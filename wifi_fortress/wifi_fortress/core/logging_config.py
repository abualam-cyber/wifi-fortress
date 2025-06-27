import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from .config_manager import ConfigManager

def setup_logging(config_manager: Optional[ConfigManager] = None) -> None:
    """
    Configure logging for WiFi Fortress
    
    Args:
        config_manager: Optional ConfigManager instance. If not provided,
                       default logging configuration will be used.
    """
    if config_manager is None:
        log_level = logging.INFO
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        log_file = 'wifi_fortress.log'
    else:
        log_level = getattr(logging, config_manager.get('logging.level', 'INFO'))
        log_format = config_manager.get('logging.format',
                                      '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = config_manager.get('logging.file', 'wifi_fortress.log')
    
    # Create logs directory if it doesn't exist
    log_dir = Path(os.path.expanduser('~/.wifi_fortress/logs'))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create handlers
    formatter = logging.Formatter(log_format)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Log startup message
    logging.info('WiFi Fortress logging initialized')
