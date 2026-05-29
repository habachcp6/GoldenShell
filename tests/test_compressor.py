"""
Unit tests for goldenshell.core.compressor module.
Tests zlib compress/decompress roundtrip and is_worth_compressing heuristic.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from goldenshell.core.compressor import compress, decompress, is_worth_compressing


# ---------------------------------------------------------------------------
# compress / decompress roundtrip
# ---------------------------------------------------------------------------


def test_compress_decompress_roundtrip():
    """compress then decompress must return the original bytes."""
    original = b"Hello, World! " * 1000
    compressed = compress(original)
    assert decompress(compressed) == original


def test_compress_reduces_size_for_repetitive_data():
    """Repetitive data should actually get smaller after compression."""
    data = b"AAAAAAAAAA" * 1000
    compressed = compress(data)
    assert len(compressed) < len(data)


def test_compress_decompress_binary_data():
    """compress/decompress should work for arbitrary binary data."""
    # Mix of text and binary bytes
    data = bytes(range(256)) * 100
    assert decompress(compress(data)) == data


def test_empty_data_compress():
    """compress of empty bytes must not raise and must be decompressible."""
    compressed = compress(b"")
    assert decompress(compressed) == b""


def test_empty_data_decompress():
    """Decompressing the compressed form of empty bytes should return b''."""
    result = decompress(compress(b""))
    assert result == b""


def test_single_byte():
    """compress/decompress roundtrip for a single byte."""
    data = b"\x42"
    assert decompress(compress(data)) == data


def test_large_data_roundtrip():
    """Roundtrip must succeed for a payload in the MB range."""
    # 2 MB of compressible text
    data = b"Lorem ipsum dolor sit amet. " * 75_000
    assert decompress(compress(data)) == data


def test_compress_different_levels():
    """All valid compression levels must produce decompressible output."""
    data = b"test data " * 500
    for level in range(1, 10):
        compressed = compress(data, level=level)
        assert decompress(compressed) == data, f"Failed at level={level}"


# ---------------------------------------------------------------------------
# is_worth_compressing
# ---------------------------------------------------------------------------


def test_is_worth_compressing_text():
    """Highly repetitive / ASCII text should be flagged as worth compressing."""
    text = b"The quick brown fox jumps over the lazy dog. " * 500
    assert is_worth_compressing(text) is True


def test_is_worth_compressing_random():
    """Pseudo-random bytes should not be worth compressing."""
    # os.urandom produces high-entropy data that zlib cannot shrink
    random_bytes = os.urandom(8192)
    assert is_worth_compressing(random_bytes) is False


def test_is_worth_compressing_empty():
    """Empty data is not worth compressing (ratio defaults to 1.0)."""
    assert is_worth_compressing(b"") is False


def test_is_worth_compressing_null_bytes():
    """Null bytes are extremely repetitive — should be worth compressing."""
    null_data = b"\x00" * 4096
    assert is_worth_compressing(null_data) is True


def test_is_worth_compressing_small_sample():
    """Function must handle data smaller than the default sample_size."""
    tiny = b"a" * 10
    # Result can be True or False, but it must not raise
    result = is_worth_compressing(tiny)
    assert isinstance(result, bool)
