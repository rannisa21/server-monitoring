"""
Encryption utility for sensitive data like SNMP passwords.
Uses Fernet symmetric encryption from cryptography library.
"""

import base64
import hashlib
from cryptography.fernet import Fernet
from flask import current_app
import logging

logger = logging.getLogger(__name__)


def _get_encryption_key():
    """
    Generate a Fernet-compatible key from the app's SECRET_KEY and ENCRYPTION_SALT.
    
    Returns:
        bytes: A 32-byte key suitable for Fernet encryption
    """
    try:
        secret_key = current_app.config.get('SECRET_KEY', 'default-secret-key')
        salt = current_app.config.get('ENCRYPTION_SALT', 'default-salt')
        
        # Combine secret key and salt, then hash to get consistent 32-byte key
        combined = f"{secret_key}{salt}".encode('utf-8')
        key = hashlib.sha256(combined).digest()
        
        # Fernet requires base64-encoded 32-byte key
        return base64.urlsafe_b64encode(key)
    except RuntimeError:
        # Outside of application context, use environment variables
        import os
        secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
        salt = os.environ.get('ENCRYPTION_SALT', 'default-salt')
        
        combined = f"{secret_key}{salt}".encode('utf-8')
        key = hashlib.sha256(combined).digest()
        return base64.urlsafe_b64encode(key)


def encrypt_password(plain_password):
    """
    Encrypt a plain text password.
    
    Args:
        plain_password: The plain text password to encrypt
        
    Returns:
        str: The encrypted password as a base64-encoded string, or None if input is None/empty
    """
    if not plain_password:
        return None
    
    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(plain_password.encode('utf-8'))
        return encrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Error encrypting password: {e}")
        raise ValueError("Failed to encrypt password")


def decrypt_password(encrypted_password):
    """
    Decrypt an encrypted password.
    
    Args:
        encrypted_password: The encrypted password (base64-encoded string)
        
    Returns:
        str: The decrypted plain text password, or None if input is None/empty
    """
    if not encrypted_password:
        return None
    
    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Error decrypting password: {e}")
        # Return None instead of raising to handle legacy unencrypted data gracefully
        return None


def is_encrypted(value):
    """
    Check if a value appears to be Fernet-encrypted.
    Fernet tokens start with 'gAAAAA' when base64 encoded.
    
    Args:
        value: The string to check
        
    Returns:
        bool: True if the value appears to be encrypted
    """
    if not value:
        return False
    
    # Fernet tokens are base64 encoded and start with version byte
    # After base64 encoding, they typically start with 'gAAAAA'
    return value.startswith('gAAAAA') and len(value) > 100
