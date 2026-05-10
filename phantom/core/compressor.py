"""
Compression module for Phantom.

Provides zlib compression/decompression for payload size reduction.
"""

import zlib


# Compression level: 6 is default, good balance of speed and ratio
DEFAULT_LEVEL = 6


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
        zlib.error: If data is not valid zlib-compressed data
    """
    return zlib.decompress(data)


def is_worth_compressing(data: bytes, sample_size: int = 4096) -> bool:
    """
    Quick check if compression is worth it by testing a sample.

    Args:
        data: Data to test
        sample_size: Size of sample to test (default 4KB)

    Returns:
        True if compression reduces size by at least 10%
    """
    sample = data[:sample_size]
    compressed_sample = zlib.compress(sample, 1)  # Fast compression for test
    ratio = len(compressed_sample) / len(sample) if len(sample) > 0 else 1.0
    return ratio < 0.90
