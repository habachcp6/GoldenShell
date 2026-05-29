"""
Integration tests for goldenshell.core.engine — hide() / extract() pipeline.

All tests exercise the full hide→extract roundtrip using real temporary files
(no mocking) to verify correctness of the entire steganography pipeline.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from goldenshell.core.engine import (
    DecryptionError,
    PayloadNotFoundError,
    extract,
    hide,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

PASSWORD = "str0ng_p@$$w0rd"


def _make_carrier(tmp_path: Path, name: str = "carrier.bin", size: int = 512) -> Path:
    """Create a dummy carrier file (random-ish but deterministic bytes)."""
    carrier = tmp_path / name
    # Use a simple repeating pattern that does NOT contain the MAGIC bytes
    carrier.write_bytes(b"CARRIER_DATA_" * (size // 13 + 1))
    return carrier


def _make_payload(tmp_path: Path, name: str, content: bytes) -> Path:
    """Write a payload file to tmp_path and return its path."""
    p = tmp_path / name
    p.write_bytes(content)
    return p


# ---------------------------------------------------------------------------
# Basic roundtrip tests
# ---------------------------------------------------------------------------


def test_hide_extract_basic(tmp_path):
    """Hide a file then extract it — data must match exactly."""
    carrier = _make_carrier(tmp_path)
    payload = _make_payload(tmp_path, "secret.txt", b"Top secret content!")
    output = tmp_path / "steg_output.bin"
    out_dir = tmp_path / "extracted"

    hide(carrier, [payload], output)
    extracted = extract(output, out_dir)

    assert len(extracted) == 1
    assert extracted[0].name == "secret.txt"
    assert extracted[0].read_bytes() == b"Top secret content!"


def test_hide_extract_with_password(tmp_path):
    """hide with password → extract with correct password → data matches."""
    carrier = _make_carrier(tmp_path)
    payload = _make_payload(tmp_path, "encrypted.txt", b"Encrypted payload data")
    output = tmp_path / "steg_enc.bin"
    out_dir = tmp_path / "extracted"

    hide(carrier, [payload], output, password=PASSWORD)
    extracted = extract(output, out_dir, password=PASSWORD)

    assert len(extracted) == 1
    assert extracted[0].read_bytes() == b"Encrypted payload data"


def test_hide_extract_wrong_password(tmp_path):
    """extract with wrong password must raise DecryptionError."""
    carrier = _make_carrier(tmp_path)
    payload = _make_payload(tmp_path, "secret.txt", b"secret")
    output = tmp_path / "steg_enc.bin"

    hide(carrier, [payload], output, password=PASSWORD)

    with pytest.raises(DecryptionError):
        extract(output, tmp_path / "out", password="wrong_password")


def test_hide_extract_no_password_on_encrypted_file(tmp_path):
    """extract without password on an encrypted file must raise DecryptionError."""
    carrier = _make_carrier(tmp_path)
    payload = _make_payload(tmp_path, "secret.txt", b"secret")
    output = tmp_path / "steg_enc.bin"

    hide(carrier, [payload], output, password=PASSWORD)

    with pytest.raises(DecryptionError):
        extract(output, tmp_path / "out")  # no password supplied


# ---------------------------------------------------------------------------
# Multi-file roundtrip
# ---------------------------------------------------------------------------


def test_hide_extract_multi_file(tmp_path):
    """Hide 2 files then extract — both files must be recovered correctly."""
    carrier = _make_carrier(tmp_path)
    p1 = _make_payload(tmp_path, "file1.txt", b"Content of file one")
    p2 = _make_payload(tmp_path, "file2.dat", b"\xDE\xAD\xBE\xEF" * 100)
    output = tmp_path / "steg_multi.bin"
    out_dir = tmp_path / "extracted"

    hide(carrier, [p1, p2], output)
    extracted = extract(output, out_dir)

    assert len(extracted) == 2
    names = {p.name for p in extracted}
    assert "file1.txt" in names
    assert "file2.dat" in names

    extracted_map = {p.name: p.read_bytes() for p in extracted}
    assert extracted_map["file1.txt"] == b"Content of file one"
    assert extracted_map["file2.dat"] == b"\xDE\xAD\xBE\xEF" * 100


def test_hide_extract_multi_file_with_password(tmp_path):
    """Multi-file hide with password → extract with password → all files correct."""
    carrier = _make_carrier(tmp_path)
    files = [
        _make_payload(tmp_path, "a.txt", b"Alpha"),
        _make_payload(tmp_path, "b.txt", b"Beta"),
        _make_payload(tmp_path, "c.txt", b"Gamma"),
    ]
    output = tmp_path / "steg_multi_enc.bin"
    out_dir = tmp_path / "extracted"

    hide(carrier, files, output, password=PASSWORD)
    extracted = extract(output, out_dir, password=PASSWORD)

    assert len(extracted) == 3
    data_map = {p.name: p.read_bytes() for p in extracted}
    assert data_map["a.txt"] == b"Alpha"
    assert data_map["b.txt"] == b"Beta"
    assert data_map["c.txt"] == b"Gamma"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_hide_empty_payload(tmp_path):
    """Hiding a 0-byte file must succeed and extract to 0 bytes."""
    carrier = _make_carrier(tmp_path)
    payload = _make_payload(tmp_path, "empty.bin", b"")
    output = tmp_path / "steg_empty.bin"
    out_dir = tmp_path / "extracted"

    hide(carrier, [payload], output)
    extracted = extract(output, out_dir)

    assert len(extracted) == 1
    assert extracted[0].read_bytes() == b""


def test_extract_no_payload(tmp_path):
    """extract on a plain file with no steg data must raise PayloadNotFoundError."""
    plain_file = tmp_path / "plain.bin"
    plain_file.write_bytes(b"This is just a normal file with no hidden payload.")

    with pytest.raises(PayloadNotFoundError):
        extract(plain_file, tmp_path / "out")


def test_extract_nonexistent_file(tmp_path):
    """extract on a non-existent file must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        extract(tmp_path / "does_not_exist.bin", tmp_path / "out")


def test_hide_carrier_not_found(tmp_path):
    """hide with a missing carrier must raise FileNotFoundError."""
    payload = _make_payload(tmp_path, "p.txt", b"data")
    with pytest.raises(FileNotFoundError):
        hide(tmp_path / "missing_carrier.bin", [payload], tmp_path / "out.bin")


def test_hide_payload_not_found(tmp_path):
    """hide with a missing payload file must raise FileNotFoundError."""
    carrier = _make_carrier(tmp_path)
    with pytest.raises(FileNotFoundError):
        hide(carrier, [tmp_path / "missing_payload.bin"], tmp_path / "out.bin")


# ---------------------------------------------------------------------------
# Carrier integrity — original content must be preserved
# ---------------------------------------------------------------------------


def test_carrier_data_preserved(tmp_path):
    """
    The first N bytes of the steg output must equal the original carrier bytes.
    Ensures hide() does not corrupt the carrier file.
    """
    carrier = _make_carrier(tmp_path, size=1024)
    payload = _make_payload(tmp_path, "data.txt", b"payload bytes")
    output = tmp_path / "steg.bin"

    carrier_bytes = carrier.read_bytes()
    hide(carrier, [payload], output)

    steg_bytes = output.read_bytes()
    assert steg_bytes[: len(carrier_bytes)] == carrier_bytes


# ---------------------------------------------------------------------------
# PayloadInfo metadata returned by hide()
# ---------------------------------------------------------------------------


def test_hide_returns_payload_info_single(tmp_path):
    """hide() must return a PayloadInfo with correct metadata for a single file."""
    carrier = _make_carrier(tmp_path)
    payload = _make_payload(tmp_path, "meta_test.txt", b"metadata check")
    output = tmp_path / "steg_meta.bin"

    info = hide(carrier, [payload], output)

    assert info.filename == "meta_test.txt"
    assert info.file_count == 1
    assert info.is_encrypted is False
    assert info.is_multi_file is False


def test_hide_returns_payload_info_encrypted(tmp_path):
    """hide() with password must set is_encrypted=True in returned PayloadInfo."""
    carrier = _make_carrier(tmp_path)
    payload = _make_payload(tmp_path, "enc_meta.txt", b"secret")
    output = tmp_path / "steg_enc_meta.bin"

    info = hide(carrier, [payload], output, password=PASSWORD)

    assert info.is_encrypted is True


def test_hide_returns_payload_info_multi(tmp_path):
    """hide() with multiple files must set is_multi_file=True in PayloadInfo."""
    carrier = _make_carrier(tmp_path)
    p1 = _make_payload(tmp_path, "f1.txt", b"data1")
    p2 = _make_payload(tmp_path, "f2.txt", b"data2")
    output = tmp_path / "steg_multi_meta.bin"

    info = hide(carrier, [p1, p2], output)

    assert info.is_multi_file is True
    assert info.file_count == 2


# ---------------------------------------------------------------------------
# Compression behavior
# ---------------------------------------------------------------------------


def test_hide_extract_compression_disabled(tmp_path):
    """Even with compression disabled, hide/extract roundtrip must succeed."""
    carrier = _make_carrier(tmp_path)
    content = b"Compressible content " * 200
    payload = _make_payload(tmp_path, "comp_off.txt", content)
    output = tmp_path / "steg_nocomp.bin"
    out_dir = tmp_path / "extracted"

    hide(carrier, [payload], output, compress_payload=False)
    extracted = extract(output, out_dir)

    assert extracted[0].read_bytes() == content
