"""
Multi-file packer module for GoldenShell.

Packs multiple files into a single binary payload and unpacks them back.

Pack format:
  [file_count: uint32]
  For each file:
    [filename_len: uint16]
    [filename: bytes]
    [data_len: uint64]
    [data: bytes]
"""

import struct
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass
class PackedFile:
    """Represents a file entry in a packed payload."""
    filename: str
    data: bytes

    @property
    def size(self) -> int:
        return len(self.data)


# Pack format constants
FILE_COUNT_FORMAT = "!I"  # uint32, 4 bytes
FILE_ENTRY_HEADER_FORMAT = "!HQ"  # uint16 fname_len + uint64 data_len = 10 bytes


def _sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.

    Strips directory components and dangerous characters,
    keeping only the basename.

    Args:
        filename: Raw filename from packed data

    Returns:
        Safe filename (basename only)

    Raises:
        ValueError: If filename is empty after sanitization
    """
    # Strip any directory components (prevents ../../etc/passwd)
    safe_name = PurePosixPath(filename).name
    # Also handle Windows-style paths
    safe_name = Path(safe_name).name
    # Remove any null bytes
    safe_name = safe_name.replace("\x00", "")

    if not safe_name:
        raise ValueError(f"Invalid filename after sanitization: {filename!r}")

    return safe_name


def pack_files(files: list[PackedFile]) -> bytes:
    """
    Pack multiple files into a single binary blob.

    Args:
        files: List of PackedFile objects to pack

    Returns:
        Packed binary data containing all files
    """
    parts = []

    # File count header
    parts.append(struct.pack(FILE_COUNT_FORMAT, len(files)))

    for f in files:
        fname_bytes = f.filename.encode("utf-8")
        fname_len = len(fname_bytes)

        # Entry header: filename length + data length
        parts.append(struct.pack(FILE_ENTRY_HEADER_FORMAT, fname_len, len(f.data)))
        # Filename
        parts.append(fname_bytes)
        # File data
        parts.append(f.data)

    return b"".join(parts)


def unpack_files(data: bytes) -> list[PackedFile]:
    """
    Unpack binary blob back into individual files.

    Args:
        data: Packed binary data

    Returns:
        List of PackedFile objects

    Raises:
        struct.error: If data format is invalid
        ValueError: If any filename is invalid after sanitization
    """
    offset = 0
    files = []

    # Read file count
    (file_count,) = struct.unpack(
        FILE_COUNT_FORMAT, data[offset : offset + struct.calcsize(FILE_COUNT_FORMAT)]
    )
    offset += struct.calcsize(FILE_COUNT_FORMAT)

    entry_header_size = struct.calcsize(FILE_ENTRY_HEADER_FORMAT)

    for _ in range(file_count):
        # Read entry header
        fname_len, data_len = struct.unpack(
            FILE_ENTRY_HEADER_FORMAT, data[offset : offset + entry_header_size]
        )
        offset += entry_header_size

        # Read and sanitize filename (prevent path traversal)
        raw_filename = data[offset : offset + fname_len].decode("utf-8")
        filename = _sanitize_filename(raw_filename)
        offset += fname_len

        # Read file data
        file_data = data[offset : offset + data_len]
        offset += data_len

        files.append(PackedFile(filename=filename, data=file_data))

    return files


def pack_from_paths(file_paths: list[Path]) -> bytes:
    """
    Read files from disk and pack them.

    Args:
        file_paths: List of file paths to read and pack

    Returns:
        Packed binary data
    """
    files = []
    for path in file_paths:
        data = path.read_bytes()
        files.append(PackedFile(filename=path.name, data=data))
    return pack_files(files)
