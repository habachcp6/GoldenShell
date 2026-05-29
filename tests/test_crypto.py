"""
Unit tests for goldenshell.core.crypto module.
Tests AES-256-GCM encrypt/decrypt roundtrip, wrong-password behavior,
checksum computation and verification.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from cryptography.exceptions import InvalidTag

from goldenshell.core.crypto import (
    compute_checksum,
    decrypt_payload,
    encrypt_payload,
    verify_checksum,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_DATA = b"The quick brown fox jumps over the lazy dog"
PASSWORD = "s3cr3t_p@ssw0rd"


# ---------------------------------------------------------------------------
# encrypt_payload / decrypt_payload
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_roundtrip():
    """encrypt then decrypt must return the original plaintext."""
    ciphertext, nonce, salt, auth_tag = encrypt_payload(SAMPLE_DATA, PASSWORD)
    result = decrypt_payload(ciphertext, nonce, salt, auth_tag, PASSWORD)
    assert result == SAMPLE_DATA


def test_encrypt_decrypt_roundtrip_empty_data():
    """encrypt/decrypt should work for zero-length plaintext."""
    empty = b""
    ciphertext, nonce, salt, auth_tag = encrypt_payload(empty, PASSWORD)
    result = decrypt_payload(ciphertext, nonce, salt, auth_tag, PASSWORD)
    assert result == empty


def test_encrypt_produces_different_ciphertext():
    """
    Two encrypt calls with the same data+password must produce different
    ciphertexts due to random nonce and salt.
    """
    ct1, nonce1, salt1, tag1 = encrypt_payload(SAMPLE_DATA, PASSWORD)
    ct2, nonce2, salt2, tag2 = encrypt_payload(SAMPLE_DATA, PASSWORD)

    # Nonces and salts should be different (random)
    assert nonce1 != nonce2 or salt1 != salt2, (
        "Two encrypt calls produced identical nonce+salt — RNG may be broken"
    )
    # Ciphertexts should differ
    assert ct1 != ct2, "Same data+password produced identical ciphertexts"


def test_wrong_password_raises():
    """Decrypting with an incorrect password must raise InvalidTag."""
    ciphertext, nonce, salt, auth_tag = encrypt_payload(SAMPLE_DATA, PASSWORD)
    with pytest.raises(InvalidTag):
        decrypt_payload(ciphertext, nonce, salt, auth_tag, "wrong_password")


def test_wrong_password_raises_unicode():
    """Decryption with a completely different unicode password must fail."""
    ciphertext, nonce, salt, auth_tag = encrypt_payload(SAMPLE_DATA, "αβγδεζη")
    with pytest.raises(InvalidTag):
        decrypt_payload(ciphertext, nonce, salt, auth_tag, "ΑΒΓΔΕΖΗ")


def test_tampered_ciphertext_raises():
    """Modifying a byte in the ciphertext must cause authentication failure."""
    ciphertext, nonce, salt, auth_tag = encrypt_payload(SAMPLE_DATA, PASSWORD)
    # Flip the first byte of ciphertext
    tampered = bytes([ciphertext[0] ^ 0xFF]) + ciphertext[1:]
    with pytest.raises(InvalidTag):
        decrypt_payload(tampered, nonce, salt, auth_tag, PASSWORD)


def test_tampered_auth_tag_raises():
    """Modifying the auth tag must cause authentication failure."""
    ciphertext, nonce, salt, auth_tag = encrypt_payload(SAMPLE_DATA, PASSWORD)
    bad_tag = bytes([auth_tag[0] ^ 0xFF]) + auth_tag[1:]
    with pytest.raises(InvalidTag):
        decrypt_payload(ciphertext, nonce, salt, bad_tag, PASSWORD)


def test_encrypt_large_data():
    """encrypt/decrypt must work for payloads larger than a few KB."""
    large = b"A" * 100_000
    ciphertext, nonce, salt, auth_tag = encrypt_payload(large, PASSWORD)
    result = decrypt_payload(ciphertext, nonce, salt, auth_tag, PASSWORD)
    assert result == large


# ---------------------------------------------------------------------------
# compute_checksum / verify_checksum
# ---------------------------------------------------------------------------


def test_checksum_correctness():
    """compute_checksum must return a 32-byte SHA-256 digest."""
    digest = compute_checksum(SAMPLE_DATA)
    assert isinstance(digest, bytes)
    assert len(digest) == 32


def test_checksum_deterministic():
    """Same data must always produce the same checksum."""
    assert compute_checksum(SAMPLE_DATA) == compute_checksum(SAMPLE_DATA)


def test_checksum_empty_data():
    """compute_checksum must handle empty bytes input."""
    digest = compute_checksum(b"")
    assert len(digest) == 32


def test_verify_checksum_pass():
    """verify_checksum must return True when data matches expected digest."""
    expected = compute_checksum(SAMPLE_DATA)
    assert verify_checksum(SAMPLE_DATA, expected) is True


def test_verify_checksum_fail():
    """verify_checksum must return False when data does not match digest."""
    expected = compute_checksum(SAMPLE_DATA)
    corrupted = SAMPLE_DATA[:-1] + bytes([SAMPLE_DATA[-1] ^ 0x01])
    assert verify_checksum(corrupted, expected) is False


def test_verify_checksum_wrong_expected():
    """verify_checksum must return False for a completely wrong expected value."""
    assert verify_checksum(SAMPLE_DATA, b"\x00" * 32) is False
