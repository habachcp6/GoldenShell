"""
Cryptographic module for Phantom.

Provides AES-256-GCM encryption/decryption with PBKDF2 key derivation.
"""

import os
import hmac
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


# Key derivation parameters
KDF_ITERATIONS = 600_000  # OWASP 2023 recommendation for PBKDF2-HMAC-SHA256
KEY_LENGTH = 32  # 256 bits
SALT_LENGTH = 16
NONCE_LENGTH = 12  # 96 bits for GCM


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit encryption key from password using PBKDF2-HMAC-SHA256.

    Args:
        password: User-provided password string
        salt: Random salt bytes (16 bytes)

    Returns:
        32-byte derived key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def generate_salt() -> bytes:
    """Generate a random 16-byte salt."""
    return os.urandom(SALT_LENGTH)


def generate_nonce() -> bytes:
    """Generate a random 12-byte nonce for AES-GCM."""
    return os.urandom(NONCE_LENGTH)


def encrypt_payload(data: bytes, password: str) -> tuple[bytes, bytes, bytes, bytes]:
    """
    Encrypt data using AES-256-GCM.

    Args:
        data: Plaintext bytes to encrypt
        password: User password for key derivation

    Returns:
        Tuple of (ciphertext_with_tag, nonce, salt, auth_tag)
        Note: AESGCM.encrypt() appends the 16-byte auth tag to the ciphertext
    """
    salt = generate_salt()
    nonce = generate_nonce()
    key = derive_key(password, salt)

    aesgcm = AESGCM(key)
    # AESGCM.encrypt returns ciphertext + 16-byte auth tag appended
    ciphertext_with_tag = aesgcm.encrypt(nonce, data, None)

    # Separate ciphertext and auth tag
    ciphertext = ciphertext_with_tag[:-16]
    auth_tag = ciphertext_with_tag[-16:]

    return ciphertext, nonce, salt, auth_tag


def decrypt_payload(
    ciphertext: bytes, nonce: bytes, salt: bytes, auth_tag: bytes, password: str
) -> bytes:
    """
    Decrypt data using AES-256-GCM.

    Args:
        ciphertext: Encrypted bytes (without auth tag)
        nonce: 12-byte nonce used during encryption
        salt: 16-byte salt used for key derivation
        auth_tag: 16-byte GCM authentication tag
        password: User password

    Returns:
        Decrypted plaintext bytes

    Raises:
        cryptography.exceptions.InvalidTag: If password is wrong or data tampered
    """
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    # AESGCM.decrypt expects ciphertext + auth_tag concatenated
    ciphertext_with_tag = ciphertext + auth_tag
    return aesgcm.decrypt(nonce, ciphertext_with_tag, None)


def compute_checksum(data: bytes) -> bytes:
    """
    Compute SHA-256 checksum of data.

    Args:
        data: Bytes to hash

    Returns:
        32-byte SHA-256 digest
    """
    return hashlib.sha256(data).digest()


def verify_checksum(data: bytes, expected: bytes) -> bool:
    """
    Verify SHA-256 checksum matches expected value.
    Uses constant-time comparison to prevent timing attacks.

    Args:
        data: Bytes to verify
        expected: Expected 32-byte SHA-256 digest

    Returns:
        True if checksum matches
    """
    return hmac.compare_digest(compute_checksum(data), expected)
