import os
import json
import base64
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class SecureConfigManager:
    """Secure configuration manager with encryption support"""
    
    def __init__(self, config_path: str, master_password: str):
        self.config_path = config_path
        self._config: Dict = {}
        self._fernet = self._setup_encryption(master_password)
        
    def _setup_encryption(self, master_password: str) -> Fernet:
        """Setup encryption using master password
        
        Args:
            master_password: Master password for deriving encryption key
            
        Returns:
            Fernet instance for encryption/decryption
        """
        # Use salt from environment or generate new one
        salt = os.environ.get('WIFI_FORTRESS_SALT', None)
        if not salt:
            salt = base64.b64encode(os.urandom(16)).decode('utf-8')
            os.environ['WIFI_FORTRESS_SALT'] = salt
        else:
            salt = salt.encode('utf-8')
            
        # Generate key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.b64encode(kdf.derive(master_password.encode()))
        return Fernet(key)
        
    def load_config(self) -> bool:
        """Load and decrypt configuration
        
        Returns:
            bool: True if config loaded successfully
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'rb') as f:
                    encrypted_data = f.read()
                    decrypted_data = self._fernet.decrypt(encrypted_data)
                    self._config = json.loads(decrypted_data)
            else:
                self._config = {}
            return True
        except Exception as e:
            logger.error(f'Error loading secure config: {e}')
            return False
            
    def save_config(self) -> bool:
        """Encrypt and save configuration
        
        Returns:
            bool: True if config saved successfully
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Encrypt and save
            config_json = json.dumps(self._config)
            encrypted_data = self._fernet.encrypt(config_json.encode())
            
            with open(self.config_path, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            logger.error(f'Error saving secure config: {e}')
            return False
            
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            # Support nested keys with dot notation
            keys = key.split('.')
            value = self._config
            for k in keys:
                value = value.get(k, {})
            return value if value != {} else default
        except Exception as e:
            logger.error(f'Error getting config value: {e}')
            return default
            
    def set_value(self, key: str, value: Any) -> bool:
        """Set configuration value
        
        Args:
            key: Configuration key
            value: Value to set
            
        Returns:
            bool: True if value was set successfully
        """
        try:
            # Support nested keys with dot notation
            keys = key.split('.')
            config = self._config
            
            # Navigate to the correct nested level
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
                
            # Set the value
            config[keys[-1]] = value
            return True
        except Exception as e:
            logger.error(f'Error setting config value: {e}')
            return False
            
    def delete_value(self, key: str) -> bool:
        """Delete configuration value
        
        Args:
            key: Configuration key
            
        Returns:
            bool: True if value was deleted successfully
        """
        try:
            keys = key.split('.')
            config = self._config
            
            # Navigate to parent of target key
            for k in keys[:-1]:
                config = config.get(k, {})
                
            # Delete the key if it exists
            if keys[-1] in config:
                del config[keys[-1]]
                return True
            return False
        except Exception as e:
            logger.error(f'Error deleting config value: {e}')
            return False
            
    def get_all_config(self) -> Dict:
        """Get entire configuration
        
        Returns:
            Dict: Copy of entire configuration
        """
        return self._config.copy()
        
    def reset_config(self) -> bool:
        """Reset configuration to empty state
        
        Returns:
            bool: True if config was reset successfully
        """
        try:
            self._config = {}
            return self.save_config()
        except Exception as e:
            logger.error(f'Error resetting config: {e}')
            return False
            
    def change_master_password(self, new_password: str) -> bool:
        """Change master password and re-encrypt configuration
        
        Args:
            new_password: New master password
            
        Returns:
            bool: True if password was changed successfully
        """
        try:
            # Create new Fernet instance with new password
            new_fernet = self._setup_encryption(new_password)
            
            # Re-encrypt config with new key
            config_json = json.dumps(self._config)
            encrypted_data = new_fernet.encrypt(config_json.encode())
            
            # Save re-encrypted config
            with open(self.config_path, 'wb') as f:
                f.write(encrypted_data)
                
            # Update instance
            self._fernet = new_fernet
            return True
        except Exception as e:
            logger.error(f'Error changing master password: {e}')
            return False
