import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config import ENCRYPTION_KEY

_FERNET_INSTANCE = None

def _get_fernet() -> Fernet:
    """Derive a Fernet key from the ENCRYPTION_KEY environment variable. Caches the instance."""
    global _FERNET_INSTANCE
    if _FERNET_INSTANCE:
        return _FERNET_INSTANCE
    
    secret = ENCRYPTION_KEY or "fallback_weak_dev_key_change_me"
    # PBKDF2 to derive a 32-byte key from the secret
    salt = b"ai_workhorse_v8_salt" # Static salt for simplicity
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    _FERNET_INSTANCE = Fernet(key)
    return _FERNET_INSTANCE

def encrypt_key(plain_text: str) -> str:
    """Encrypt a plain text string to a URL-safe base64 string."""
    if not plain_text:
        return ""
    try:
        f = _get_fernet()
        return f.encrypt(plain_text.encode()).decode()
    except Exception:
        return ""

def decrypt_key(encrypted_text: str) -> str:
    """Decrypt an encrypted string. Returns empty string on failure."""
    if not encrypted_text:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_text.encode()).decode()
    except Exception:
        return ""

def verify_encryption_setup():
    """Verify the encryption setup by doing a test encryption/decryption loop."""
    test_str = "ai_workhorse_test_vector"
    encrypted = encrypt_key(test_str)
    decrypted = decrypt_key(encrypted)
    if decrypted != test_str:
        raise RuntimeError("Encryption verification failed. Possible key mismatch.")
