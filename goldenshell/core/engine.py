"""
Main engine module for GoldenShell.

Provides high-level hide/extract operations
by orchestrating the protocol, crypto, compression, and packer modules.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .steg_protocol import (
    MAGIC,
    FOOTER_MAGIC,
    AUTH_TAG_SIZE,
    StegFlags,
    StegHeader,
    find_footer,
    find_magic,
)
from .crypto import (
    encrypt_payload,
    decrypt_payload,
    compute_checksum,
    verify_checksum,
)
from .compressor import compress, decompress, is_worth_compressing
from .packer import PackedFile, pack_files, unpack_files, pack_from_paths


class GoldenShellError(Exception):
    """Base exception for GoldenShell operations."""
    pass


class PayloadNotFoundError(GoldenShellError):
    """Raised when no hidden payload is found in a file."""
    pass


class IntegrityError(GoldenShellError):
    """Raised when payload checksum verification fails."""
    pass


class DecryptionError(GoldenShellError):
    """Raised when decryption fails (wrong password or tampered data)."""
    pass


@dataclass
class PayloadInfo:
    """Metadata about a hidden payload."""
    filename: str
    payload_size: int
    is_encrypted: bool
    is_compressed: bool
    is_multi_file: bool
    checksum_hex: str
    version: int
    carrier_size: int  # size of original carrier (before payload)

    # Multi-file details (only populated for multi-file payloads after extract)
    file_count: int = 0
    file_names: list[str] = None

    def __post_init__(self):
        if self.file_names is None:
            self.file_names = []


def hide(
    carrier_path: str | Path,
    payload_paths: list[str | Path],
    output_path: str | Path,
    password: Optional[str] = None,
    compress_payload: bool = True,
) -> PayloadInfo:
    """
    Hide one or more files inside a carrier file.

    Args:
        carrier_path: Path to the carrier file (PDF, PNG, JPEG, etc.)
        payload_paths: List of file paths to hide
        output_path: Path for the output file
        password: Optional password for AES-256-GCM encryption
        compress_payload: Whether to compress the payload (default True)

    Returns:
        PayloadInfo with metadata about the hidden payload

    Raises:
        FileNotFoundError: If carrier or payload files don't exist
        GoldenShellError: If operation fails
    """
    carrier_path = Path(carrier_path)
    output_path = Path(output_path)
    payload_paths = [Path(p) for p in payload_paths]

    # Validate inputs
    if not carrier_path.exists():
        raise FileNotFoundError(f"Carrier file not found: {carrier_path}")
    for p in payload_paths:
        if not p.exists():
            raise FileNotFoundError(f"Payload file not found: {p}")

    # Read carrier
    carrier_data = carrier_path.read_bytes()

    # Prepare payload
    is_multi = len(payload_paths) > 1
    if is_multi:
        raw_payload = pack_from_paths(payload_paths)
        primary_filename = f"{len(payload_paths)}_files.pack"
    else:
        raw_payload = payload_paths[0].read_bytes()
        primary_filename = payload_paths[0].name

    # Compute checksum of original data
    checksum = compute_checksum(raw_payload)

    # Build flags
    flags = StegFlags.NONE
    if is_multi:
        flags |= StegFlags.MULTI_FILE

    # Compress if beneficial
    if compress_payload and is_worth_compressing(raw_payload):
        raw_payload = compress(raw_payload)
        flags |= StegFlags.COMPRESSED

    # Encrypt if password provided
    nonce = b"\x00" * 12
    salt = b"\x00" * 16
    auth_tag = b""

    if password:
        ciphertext, nonce, salt, auth_tag = encrypt_payload(raw_payload, password)
        raw_payload = ciphertext
        flags |= StegFlags.ENCRYPTED

    # Build header
    header = StegHeader(
        flags=int(flags),
        nonce=nonce,
        salt=salt,
        filename=primary_filename,
        payload_size=len(raw_payload),
        checksum=checksum,
    )

    # Assemble output: carrier + MAGIC + header + payload + [auth_tag] + FOOTER
    parts = [
        carrier_data,
        MAGIC,
        header.pack(),
        raw_payload,
    ]

    if password:
        parts.append(auth_tag)

    parts.append(FOOTER_MAGIC)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"".join(parts))

    return PayloadInfo(
        filename=primary_filename,
        payload_size=header.payload_size,
        is_encrypted=header.is_encrypted,
        is_compressed=header.is_compressed,
        is_multi_file=header.is_multi_file,
        checksum_hex=checksum.hex(),
        version=header.version,
        carrier_size=len(carrier_data),
        file_count=len(payload_paths),
        file_names=[p.name for p in payload_paths],
    )


def extract(
    steg_file_path: str | Path,
    output_dir: str | Path,
    password: Optional[str] = None,
) -> list[Path]:
    """
    Extract hidden payload from a steganography file.

    Args:
        steg_file_path: Path to the file containing hidden data
        output_dir: Directory to write extracted files
        password: Password for decryption (if encrypted)

    Returns:
        List of paths to extracted files

    Raises:
        PayloadNotFoundError: If no hidden payload is found
        DecryptionError: If password is wrong
        IntegrityError: If checksum verification fails
    """
    steg_file_path = Path(steg_file_path)
    output_dir = Path(output_dir)

    if not steg_file_path.exists():
        raise FileNotFoundError(f"File not found: {steg_file_path}")

    file_data = steg_file_path.read_bytes()

    # Find footer
    footer_pos = find_footer(file_data)
    if footer_pos is None:
        raise PayloadNotFoundError(f"No hidden payload found in: {steg_file_path}")

    # Find magic
    magic_pos = find_magic(file_data)
    if magic_pos is None:
        raise PayloadNotFoundError(f"No GoldenShell magic found in: {steg_file_path}")

    # Parse header
    header_data = file_data[magic_pos:]
    header = StegHeader.unpack(header_data)

    # Extract raw payload (after header, before auth_tag/footer)
    payload_start = magic_pos + header.packed_size()

    if header.is_encrypted:
        payload_end = payload_start + header.payload_size
        raw_payload = file_data[payload_start:payload_end]
        auth_tag = file_data[payload_end : payload_end + AUTH_TAG_SIZE]
    else:
        payload_end = payload_start + header.payload_size
        raw_payload = file_data[payload_start:payload_end]
        auth_tag = b""

    # Decrypt if needed
    if header.is_encrypted:
        if not password:
            raise DecryptionError("File is encrypted. Password required.")
        try:
            from cryptography.exceptions import InvalidTag

            raw_payload = decrypt_payload(
                raw_payload, header.nonce, header.salt, auth_tag, password
            )
        except InvalidTag:
            raise DecryptionError(
                "Decryption failed. Wrong password or data has been tampered."
            )

    # Decompress if needed
    if header.is_compressed:
        raw_payload = decompress(raw_payload)

    # Verify checksum
    if not verify_checksum(raw_payload, header.checksum):
        raise IntegrityError(
            "Checksum mismatch! Extracted data may be corrupted or tampered."
        )

    # Write extracted files
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_paths = []

    if header.is_multi_file:
        packed_files = unpack_files(raw_payload)
        for pf in packed_files:
            out_path = output_dir / pf.filename
            out_path.write_bytes(pf.data)
            extracted_paths.append(out_path)
    else:
        out_path = output_dir / header.filename
        out_path.write_bytes(raw_payload)
        extracted_paths.append(out_path)

    return extracted_paths
