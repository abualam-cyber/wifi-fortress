"""Security module for WiFi Fortress.

This module provides core security functionality including:
- Secure storage for credentials and configurations
- Encryption/decryption utilities
- Plugin validation and sandboxing
- Input validation and sanitization
"""

import os
import hmac
import json
import logging
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from .error_handler import SecurityError, handle_errors

logger = logging.getLogger(__name__)

class SecurityManager:
    """Manages security operations for WiFi Fortress"""
    
    def __init__(self, config_dir: Union[str, Path]):
        """Initialize security manager
        
        Args:
            config_dir: Directory for security configuration files
        """
        self.config_dir = Path(config_dir)
        self.key_file = self.config_dir / 'master.key'
        self.salt_file = self.config_dir / 'salt'
        self.whitelist_file = self.config_dir / 'plugin_whitelist.json'
        self.blacklist_file = self.config_dir / 'plugin_blacklist.json'
        self.fernet = self._initialize_encryption()
        
        # Initialize plugin hash lists
        self._load_hash_lists()
        
    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption with master key"""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate or load salt
            if not self.salt_file.exists():
                salt = os.urandom(16)
                with open(self.salt_file, 'wb') as f:
                    f.write(salt)
            else:
                with open(self.salt_file, 'rb') as f:
                    salt = f.read()
            
            # Generate or load master key
            if not self.key_file.exists():
                # Generate a new master key
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                key = b64encode(kdf.derive(os.urandom(32)))
                # Save key securely
                with open(self.key_file, 'wb') as f:
                    f.write(key)
            else:
                # Load existing key
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                    
            return Fernet(key)
            
        except Exception as e:
            msg = f'Failed to initialize encryption: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
    
    def encrypt_data(self, data: Union[str, bytes, dict]) -> bytes:
        """Encrypt data using Fernet encryption
        
        Args:
            data: Data to encrypt (string, bytes, or dict)
            
        Returns:
            bytes: Encrypted data
            
        Raises:
            SecurityError: If encryption fails
        """
        try:
            # Convert data to bytes
            if isinstance(data, dict):
                data = json.dumps(data).encode()
            elif isinstance(data, str):
                data = data.encode()
                
            # Encrypt data
            return self.fernet.encrypt(data)
            
        except Exception as e:
            msg = f'Failed to encrypt data: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
    
    def decrypt_data(self, encrypted_data: bytes) -> Union[str, dict]:
        """Decrypt data using Fernet encryption
        
        Args:
            encrypted_data: Data to decrypt
            
        Returns:
            Union[str, dict]: Decrypted data
            
        Raises:
            SecurityError: If decryption fails
        """
        try:
            # Decrypt data
            decrypted = self.fernet.decrypt(encrypted_data)
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted)
            except json.JSONDecodeError:
                return decrypted.decode()
                
        except Exception as e:
            msg = f'Failed to decrypt data: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
    
    def validate_plugin(self, plugin_path: Union[str, Path]) -> bool:
        """Validate a plugin's integrity and safety
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            bool: True if plugin is safe
            
        Raises:
            SecurityError: If validation fails or plugin is unsafe
        """
        try:
            plugin_path = Path(plugin_path)
            
            # Check if file exists
            if not plugin_path.exists():
                raise SecurityError(f'Plugin file not found: {plugin_path}')
            
            # Read plugin content
            with open(plugin_path, 'rb') as f:
                content = f.read()
            
            # Check for dangerous imports
            dangerous_imports = [
                'os.system', 'subprocess.', 'eval(', 'exec(',
                'import socket', 'import requests'
            ]
            
            content_str = content.decode('utf-8')
            for imp in dangerous_imports:
                if imp in content_str:
                    raise SecurityError(
                        f'Plugin contains potentially dangerous code: {imp}'
                    )
            
                # Calculate plugin hash
            plugin_hash = hashlib.sha256(content).hexdigest()
            
            # Check against blacklist
            if plugin_hash in self.blacklist:
                raise SecurityError(f'Plugin hash {plugin_hash} is blacklisted')
            
            # Check whitelist if enabled
            if self.whitelist and plugin_hash not in self.whitelist:
                raise SecurityError(f'Plugin hash {plugin_hash} not in whitelist')
            
            return True
            
        except SecurityError:
            raise
        except Exception as e:
            msg = f'Plugin validation failed: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize user input to prevent injection attacks
        
        Args:
            data: Input data to sanitize
            
        Returns:
            Any: Sanitized data
            
        Raises:
            SecurityError: If sanitization fails
        """
        try:
            if isinstance(data, str):
                # Remove potentially dangerous characters
                dangerous_chars = ['<', '>', ';', '&', '|', '`']
                for char in dangerous_chars:
                    data = data.replace(char, '')
                return data
            elif isinstance(data, dict):
                return {
                    self.sanitize_input(k): self.sanitize_input(v)
                    for k, v in data.items()
                }
            elif isinstance(data, list):
                return [self.sanitize_input(item) for item in data]
            else:
                return data
                
        except Exception as e:
            msg = f'Input sanitization failed: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
    
    def verify_signature(self, data: bytes, signature: bytes, key: bytes) -> bool:
        """Verify digital signature of data
        
        Args:
            data: Data to verify
            signature: Signature to verify against
            key: Key used for verification
            
        Returns:
            bool: True if signature is valid
            
        Raises:
            SecurityError: If verification fails
        """
        try:
            h = hmac.new(key, data, hashlib.sha256)
            return hmac.compare_digest(h.digest(), signature)
        except Exception as e:
            msg = f'Signature verification failed: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
            
    def _load_hash_lists(self) -> None:
        """Load plugin hash whitelist and blacklist"""
        try:
            # Load whitelist
            self.whitelist = set()
            if self.whitelist_file.exists():
                with open(self.whitelist_file, 'r') as f:
                    whitelist_data = json.load(f)
                    self.whitelist.update(whitelist_data.get('hashes', []))
            
            # Load blacklist
            self.blacklist = set()
            if self.blacklist_file.exists():
                with open(self.blacklist_file, 'r') as f:
                    blacklist_data = json.load(f)
                    self.blacklist.update(blacklist_data.get('hashes', []))
                    
        except Exception as e:
            msg = f'Failed to load hash lists: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
            
    def add_to_whitelist(self, plugin_hash: str) -> None:
        """Add a plugin hash to the whitelist
        
        Args:
            plugin_hash: SHA-256 hash of the plugin file
            
        Raises:
            SecurityError: If adding to whitelist fails
        """
        try:
            self.whitelist.add(plugin_hash)
            whitelist_data = {'hashes': list(self.whitelist)}
            with open(self.whitelist_file, 'w') as f:
                json.dump(whitelist_data, f, indent=2)
        except Exception as e:
            msg = f'Failed to add to whitelist: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
            
    def add_to_blacklist(self, plugin_hash: str) -> None:
        """Add a plugin hash to the blacklist
        
        Args:
            plugin_hash: SHA-256 hash of the plugin file
            
        Raises:
            SecurityError: If adding to blacklist fails
        """
        try:
            self.blacklist.add(plugin_hash)
            blacklist_data = {'hashes': list(self.blacklist)}
            with open(self.blacklist_file, 'w') as f:
                json.dump(blacklist_data, f, indent=2)
        except Exception as e:
            msg = f'Failed to add to blacklist: {str(e)}'
            logger.error(msg)
            raise SecurityError(msg)
