"""
Compression module for GoldenShell.

Provides zlib compression/decompression for payload size reduction.
"""

import zlib


# Compression level: 6 is default, good balance of speed and ratio
DEFAULT_LEVEL = 6


class CompressionError(Exception):
    """Raised when decompression fails due to invalid or corrupted data."""
    pass


def compress(data: bytes, level: int = DEFAULT_LEVEL) -> bytes:
    """
    Compress data using zlib.

    Args:
        data: Raw bytes to compress
        level: Compression level (1=fastest, 9=smallest, 6=default)

    Returns:
        Compressed bytes
    """
    return zlib.compress(data, level)


def decompress(data: bytes) -> bytes:
    """
    Decompress zlib-compressed data.

    Args:
        data: Compressed bytes

    Returns:
        Decompressed bytes

    Raises:
        CompressionError: If data is not valid zlib-compressed data (wraps zlib.error)
    """
    # BUG-003 FIX: Wrap zlib.error so callers receive a meaningful GoldenShell-level exception
    # instead of a raw low-level error that bypasses the existing except chains in engine.py.
    try:
        return zlib.decompress(data)
    except zlib.error as exc:
        raise CompressionError(f"Failed to decompress payload: {exc}") from exc


def is_worth_compressing(data: bytes, sample_size: int = 4096) -> bool:
    """
    Quick check if compression is worth it by testing a sample.

    Args:
        data: Data to test
        sample_size: Size of sample to test (default 4KB)

    Returns:
        True if compression reduces size by at least 10%.
        Returns False immediately for empty data (nothing to compress).
    """
    # BUG-003 FIX: Return False immediately for empty data.
    # zlib.compress(b"") produces 8 bytes of overhead, so the ratio would be
    # inf/undefined and compression would silently bloat the payload.
    if not data:
        return False
    sample = data[:sample_size]
    compressed_sample = zlib.compress(sample, 1)  # Fast compression for test
    ratio = len(compressed_sample) / len(sample)
    return ratio < 0.90
