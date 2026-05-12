"""
STEG Binary Protocol definition for GoldenShell.

Defines the binary format used to embed hidden payloads inside carrier files.
Protocol layout:
  [Carrier Data] + [MAGIC] + [Header] + [Payload] + [AUTH_TAG?] + [FOOTER_MAGIC]
"""

import struct
from dataclasses import dataclass, field
from enum import IntFlag
from typing import Optional

# Magic bytes to identify GoldenShell payloads
MAGIC = b"\x00PHANTOM\xff"  # 9 bytes (kept for backward compatibility)
FOOTER_MAGIC = b"\xff\x00PHTM\xff\x00"  # 8 bytes (kept for backward compatibility)
PROTOCOL_VERSION = 1

# Header struct format (fixed part):
#   version:  uint8   (1 byte)
#   flags:    uint8   (1 byte)
#   nonce:    12 bytes
#   salt:     16 bytes
#   fname_len: uint16 (2 bytes)
# Then variable: filename (fname_len bytes)
#   payload_size: uint64 (8 bytes)
#   checksum: 32 bytes (SHA-256)
HEADER_FIXED_FORMAT = "!BB12s16sH"
HEADER_FIXED_SIZE = struct.calcsize(HEADER_FIXED_FORMAT)  # 1+1+12+16+2 = 32

PAYLOAD_META_FORMAT = "!Q32s"
PAYLOAD_META_SIZE = struct.calcsize(PAYLOAD_META_FORMAT)  # 8+32 = 40

# AES-GCM auth tag size
AUTH_TAG_SIZE = 16


class StegFlags(IntFlag):
    """Bitfield flags for STEG header."""
    NONE = 0x00
    ENCRYPTED = 0x01
    COMPRESSED = 0x02
    MULTI_FILE = 0x04


@dataclass
class StegHeader:
    """Represents the metadata header of a GoldenShell payload."""
    version: int = PROTOCOL_VERSION
    flags: int = StegFlags.NONE
    nonce: bytes = field(default_factory=lambda: b"\x00" * 12)
    salt: bytes = field(default_factory=lambda: b"\x00" * 16)
    filename: str = ""
    payload_size: int = 0
    checksum: bytes = field(default_factory=lambda: b"\x00" * 32)

    @property
    def is_encrypted(self) -> bool:
        return bool(self.flags & StegFlags.ENCRYPTED)

    @property
    def is_compressed(self) -> bool:
        return bool(self.flags & StegFlags.COMPRESSED)

    @property
    def is_multi_file(self) -> bool:
        return bool(self.flags & StegFlags.MULTI_FILE)

    def pack(self) -> bytes:
        """Serialize header to bytes."""
        fname_bytes = self.filename.encode("utf-8")
        fname_len = len(fname_bytes)

        # Fixed part
        fixed = struct.pack(
            HEADER_FIXED_FORMAT,
            self.version,
            self.flags,
            self.nonce,
            self.salt,
            fname_len,
        )

        # Variable filename
        # Payload metadata
        meta = struct.pack(
            PAYLOAD_META_FORMAT,
            self.payload_size,
            self.checksum,
        )

        return fixed + fname_bytes + meta

    @classmethod
    def unpack(cls, data: bytes) -> "StegHeader":
        """Deserialize header from bytes."""
        # Parse fixed part
        version, flags, nonce, salt, fname_len = struct.unpack(
            HEADER_FIXED_FORMAT, data[:HEADER_FIXED_SIZE]
        )

        offset = HEADER_FIXED_SIZE

        # Parse filename
        filename = data[offset : offset + fname_len].decode("utf-8")
        offset += fname_len

        # Parse payload metadata
        payload_size, checksum = struct.unpack(
            PAYLOAD_META_FORMAT, data[offset : offset + PAYLOAD_META_SIZE]
        )

        return cls(
            version=version,
            flags=flags,
            nonce=nonce,
            salt=salt,
            filename=filename,
            payload_size=payload_size,
            checksum=checksum,
        )

    def packed_size(self) -> int:
        """Return total size of packed header in bytes."""
        fname_len = len(self.filename.encode("utf-8"))
        return HEADER_FIXED_SIZE + fname_len + PAYLOAD_META_SIZE


def find_footer(data: bytes) -> Optional[int]:
    """
    Search for FOOTER_MAGIC in data (from the end).
    Returns the start position of the footer, or None if not found.
    """
    idx = data.rfind(FOOTER_MAGIC)
    return idx if idx != -1 else None


def find_magic(data: bytes, search_start: int = 0) -> Optional[int]:
    """
    Search for MAGIC bytes in data.
    Returns position after the magic, or None if not found.
    """
    idx = data.find(MAGIC, search_start)
    if idx == -1:
        return None
    return idx + len(MAGIC)
