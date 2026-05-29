# Test Summary — GoldenShell Unit Tests

> Được tạo bởi: Test Engineer Agent  
> Ngày: 2026-05-20  
> Mục tiêu: Verify tính đúng đắn của hide/extract pipeline

---

## 📁 Cấu trúc thư mục tests/

```
tests/
├── __init__.py          — Package init (rỗng)
├── test_crypto.py       — Tests cho crypto module (AES-256-GCM)
├── test_compressor.py   — Tests cho compression module (zlib)
├── test_packer.py       — Tests cho multi-file packer module
└── test_engine.py       — Integration tests cho hide/extract pipeline
```

---

## 📋 Danh sách Test Cases

### `test_crypto.py` — 12 tests

| Test | Mô tả |
|---|---|
| `test_encrypt_decrypt_roundtrip` | encrypt → decrypt trả về data gốc |
| `test_encrypt_decrypt_roundtrip_empty_data` | Roundtrip với plaintext rỗng |
| `test_encrypt_produces_different_ciphertext` | Cùng data+password → ciphertext khác (random nonce/salt) |
| `test_wrong_password_raises` | Decrypt với password sai → `InvalidTag` |
| `test_wrong_password_raises_unicode` | Password unicode sai → `InvalidTag` |
| `test_tampered_ciphertext_raises` | Ciphertext bị sửa → `InvalidTag` |
| `test_tampered_auth_tag_raises` | Auth tag bị sửa → `InvalidTag` |
| `test_encrypt_large_data` | Roundtrip với payload 100KB |
| `test_checksum_correctness` | `compute_checksum` trả về 32 bytes SHA-256 |
| `test_checksum_deterministic` | Cùng data → cùng checksum |
| `test_checksum_empty_data` | Checksum data rỗng không raise |
| `test_verify_checksum_pass` | `verify_checksum` đúng → True |
| `test_verify_checksum_fail` | `verify_checksum` data bị corrupt → False |
| `test_verify_checksum_wrong_expected` | Expected sai hoàn toàn → False |

### `test_compressor.py` — 11 tests

| Test | Mô tả |
|---|---|
| `test_compress_decompress_roundtrip` | compress → decompress trả về data gốc |
| `test_compress_reduces_size_for_repetitive_data` | Data lặp thực sự nhỏ hơn sau compress |
| `test_compress_decompress_binary_data` | Roundtrip binary data tùy ý |
| `test_empty_data_compress` | compress data rỗng không raise |
| `test_empty_data_decompress` | compress(b"") → decompress → b"" |
| `test_single_byte` | Roundtrip 1 byte |
| `test_large_data_roundtrip` | Roundtrip data 2MB |
| `test_compress_different_levels` | Mọi level 1–9 đều cho output hợp lệ |
| `test_is_worth_compressing_text` | ASCII text → True |
| `test_is_worth_compressing_random` | os.urandom bytes → False |
| `test_is_worth_compressing_empty` | Data rỗng → False |
| `test_is_worth_compressing_null_bytes` | Null bytes (rất compressible) → True |
| `test_is_worth_compressing_small_sample` | Data nhỏ hơn sample_size không raise |

### `test_packer.py` — 14 tests

| Test | Mô tả |
|---|---|
| `test_pack_unpack_single_file` | Pack 1 file → unpack → đúng |
| `test_pack_unpack_multiple_files` | Pack 3 files → unpack → đúng |
| `test_pack_preserves_binary_data` | Binary data + null bytes sống sót |
| `test_pack_preserves_filename_with_spaces` | Filename có spaces giữ nguyên |
| `test_pack_unpack_unicode_filename` | Unicode filename sống sót |
| `test_empty_data_file` | File 0 bytes pack/unpack đúng |
| `test_pack_many_files` | Pack/unpack 50 files |
| `test_path_traversal_unix_style` | `../../etc/passwd` → `passwd` |
| `test_path_traversal_windows_style` | Windows backslash traversal → basename |
| `test_path_traversal_absolute_unix` | `/etc/shadow` → `shadow` |
| `test_path_traversal_protection` | Tên sau sanitize không escape output dir |
| `test_pack_from_paths_single` | `pack_from_paths` với 1 file thật |
| `test_pack_from_paths_multiple` | `pack_from_paths` với nhiều files thật |
| `test_packed_file_size_property` | `PackedFile.size` đúng |
| `test_packed_file_size_empty` | `PackedFile.size == 0` khi data rỗng |

### `test_engine.py` — 18 tests

| Test | Mô tả |
|---|---|
| `test_hide_extract_basic` | hide → extract → data khớp |
| `test_hide_extract_with_password` | hide + password → extract + password → đúng |
| `test_hide_extract_wrong_password` | extract password sai → `DecryptionError` |
| `test_hide_extract_no_password_on_encrypted_file` | extract không password → `DecryptionError` |
| `test_hide_extract_multi_file` | hide 2 files → extract → cả 2 đúng |
| `test_hide_extract_multi_file_with_password` | Multi-file + password roundtrip |
| `test_hide_empty_payload` | hide file 0 bytes → extract → 0 bytes |
| `test_extract_no_payload` | extract file bình thường → `PayloadNotFoundError` |
| `test_extract_nonexistent_file` | extract file không tồn tại → `FileNotFoundError` |
| `test_hide_carrier_not_found` | hide carrier không tồn tại → `FileNotFoundError` |
| `test_hide_payload_not_found` | hide payload không tồn tại → `FileNotFoundError` |
| `test_carrier_data_preserved` | N bytes đầu output == carrier gốc |
| `test_hide_returns_payload_info_single` | PayloadInfo metadata đúng (single file) |
| `test_hide_returns_payload_info_encrypted` | `is_encrypted=True` khi dùng password |
| `test_hide_returns_payload_info_multi` | `is_multi_file=True`, `file_count=2` |
| `test_hide_extract_compression_disabled` | `compress_payload=False` vẫn roundtrip đúng |

---

## 🔢 Tổng cộng

| Module | Số tests |
|---|---|
| `test_crypto.py` | 14 |
| `test_compressor.py` | 13 |
| `test_packer.py` | 15 |
| `test_engine.py` | 16 |
| **Tổng** | **58 tests** |

---

## 🚀 Cách chạy

```bash
# Chạy toàn bộ test suite
python -m pytest tests/ -v

# Chạy một file cụ thể
python -m pytest tests/test_crypto.py -v

# Chạy với output tắt (chỉ hiện kết quả)
python -m pytest tests/ -q

# Chạy test theo tên
python -m pytest tests/ -k "roundtrip" -v
```

> **Yêu cầu**: `pip install pytest cryptography`

---

## ⚠️ Ghi chú kỹ thuật

1. **KDF iterations cao**: `test_crypto.py` dùng PBKDF2 với 600,000 iterations (OWASP 2023). Mỗi encrypt/decrypt call mất ~0.3–1s. Tests có nhiều encrypt/decrypt calls nên tổng thời gian chạy `test_crypto.py` và `test_engine.py` có thể **15–60 giây** tùy CPU.
2. **Không có mock**: Tất cả tests chạy với data thật và file thật (dùng `tmp_path` fixture của pytest).
3. **`test_encrypt_produces_different_ciphertext`**: Test này phụ thuộc vào `os.urandom` thực sự tạo ra giá trị khác nhau — edge case lý thuyết nếu RNG bị broken nhưng thực tế không xảy ra.

---

## STATUS: DONE
