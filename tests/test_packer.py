"""
Unit tests for goldenshell.core.packer module.
Tests pack/unpack roundtrip for single and multiple files,
path-traversal sanitization, and edge cases like empty file data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from goldenshell.core.packer import (
    PackedFile,
    pack_files,
    pack_from_paths,
    unpack_files,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_file(name: str, data: bytes) -> PackedFile:
    return PackedFile(filename=name, data=data)


# ---------------------------------------------------------------------------
# pack_files / unpack_files roundtrip
# ---------------------------------------------------------------------------


def test_pack_unpack_single_file():
    """Pack one file then unpack — content and filename must match."""
    original = _make_file("hello.txt", b"Hello, World!")
    packed = pack_files([original])
    result = unpack_files(packed)

    assert len(result) == 1
    assert result[0].filename == "hello.txt"
    assert result[0].data == b"Hello, World!"


def test_pack_unpack_multiple_files():
    """Pack three files then unpack — all files must be recovered correctly."""
    files = [
        _make_file("alpha.txt", b"Alpha content"),
        _make_file("beta.bin", bytes(range(256))),
        _make_file("gamma.dat", b"G" * 4096),
    ]
    packed = pack_files(files)
    result = unpack_files(packed)

    assert len(result) == 3
    for original, recovered in zip(files, result):
        assert recovered.filename == original.filename
        assert recovered.data == original.data


def test_pack_preserves_binary_data():
    """Binary data including null bytes must survive pack/unpack intact."""
    data = bytes([0x00, 0xFF, 0xDE, 0xAD, 0xBE, 0xEF] * 500)
    files = [_make_file("binary.bin", data)]
    result = unpack_files(pack_files(files))
    assert result[0].data == data


def test_pack_preserves_filename_with_spaces():
    """Filenames with spaces should survive pack/unpack unchanged."""
    pf = _make_file("my file name.txt", b"content")
    result = unpack_files(pack_files([pf]))
    assert result[0].filename == "my file name.txt"


def test_pack_unpack_unicode_filename():
    """Unicode filenames must survive pack/unpack."""
    pf = _make_file("données_réseau.csv", b"col1,col2\n1,2\n")
    result = unpack_files(pack_files([pf]))
    assert result[0].filename == "données_réseau.csv"


def test_empty_data_file():
    """A file with 0-byte content must pack and unpack without error."""
    pf = _make_file("empty.bin", b"")
    result = unpack_files(pack_files([pf]))
    assert len(result) == 1
    assert result[0].filename == "empty.bin"
    assert result[0].data == b""


def test_pack_many_files():
    """Pack/unpack should work with a larger number of files (50)."""
    files = [_make_file(f"file_{i:03d}.txt", f"content_{i}".encode()) for i in range(50)]
    result = unpack_files(pack_files(files))
    assert len(result) == 50
    for i, recovered in enumerate(result):
        assert recovered.filename == f"file_{i:03d}.txt"
        assert recovered.data == f"content_{i}".encode()


# ---------------------------------------------------------------------------
# Path-traversal sanitization
# ---------------------------------------------------------------------------


def test_path_traversal_unix_style():
    """'../../etc/passwd' must be sanitized to 'passwd'."""
    # Build raw packed bytes manually so _sanitize_filename is exercised on unpack
    pf = _make_file("../../etc/passwd", b"root:x:0:0")
    packed = pack_files([pf])
    result = unpack_files(packed)
    assert result[0].filename == "passwd"


def test_path_traversal_windows_style():
    """'..\\..\\ Windows\\system32\\evil.dll' must be sanitized to 'evil.dll'."""
    pf = _make_file("..\\..\\Windows\\system32\\evil.dll", b"MZ\x90\x00")
    packed = pack_files([pf])
    result = unpack_files(packed)
    assert result[0].filename == "evil.dll"


def test_path_traversal_absolute_unix():
    """/etc/shadow must be sanitized to 'shadow'."""
    pf = _make_file("/etc/shadow", b"data")
    packed = pack_files([pf])
    result = unpack_files(packed)
    assert result[0].filename == "shadow"


def test_path_traversal_protection(tmp_path):
    """
    Verifies that unpack_files sanitizes traversal paths so the recovered
    filename is safe to use when writing under a target directory.
    """
    dangerous_name = "../../etc/passwd"
    pf = _make_file(dangerous_name, b"root:x:0:0")
    packed = pack_files([pf])

    result = unpack_files(packed)
    safe_name = result[0].filename

    # Writing to tmp_path / safe_name must NOT escape tmp_path
    out = tmp_path / safe_name
    assert out.parent == tmp_path, (
        f"Filename '{safe_name}' would escape the output directory"
    )


# ---------------------------------------------------------------------------
# pack_from_paths — disk integration
# ---------------------------------------------------------------------------


def test_pack_from_paths_single(tmp_path):
    """pack_from_paths reads a real file from disk and packs it correctly."""
    src = tmp_path / "source.txt"
    src.write_bytes(b"Hello from disk!")

    packed = pack_from_paths([src])
    result = unpack_files(packed)

    assert len(result) == 1
    assert result[0].filename == "source.txt"
    assert result[0].data == b"Hello from disk!"


def test_pack_from_paths_multiple(tmp_path):
    """pack_from_paths handles multiple disk files."""
    files_data = {
        "a.txt": b"file A",
        "b.txt": b"file B",
        "c.bin": bytes(range(128)),
    }
    paths = []
    for name, content in files_data.items():
        p = tmp_path / name
        p.write_bytes(content)
        paths.append(p)

    packed = pack_from_paths(paths)
    result = unpack_files(packed)

    assert len(result) == 3
    for recovered in result:
        assert recovered.data == files_data[recovered.filename]


# ---------------------------------------------------------------------------
# PackedFile properties
# ---------------------------------------------------------------------------


def test_packed_file_size_property():
    """PackedFile.size must equal len(data)."""
    pf = _make_file("x.bin", b"12345")
    assert pf.size == 5


def test_packed_file_size_empty():
    """PackedFile.size must be 0 for empty data."""
    pf = _make_file("empty.bin", b"")
    assert pf.size == 0
