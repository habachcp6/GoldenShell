# Test Results
Date: 2026-05-20
Interpreter: d:\CTF-test\.venv\Scripts\python.exe (Python 3.13.0)
pytest: 9.0.3

## test_compressor.py
PASSED: 13/13
FAILED: none

| Test | Status |
|------|--------|
| test_compress_decompress_roundtrip | ✅ PASSED |
| test_compress_reduces_size_for_repetitive_data | ✅ PASSED |
| test_compress_decompress_binary_data | ✅ PASSED |
| test_empty_data_compress | ✅ PASSED |
| test_empty_data_decompress | ✅ PASSED |
| test_single_byte | ✅ PASSED |
| test_large_data_roundtrip | ✅ PASSED |
| test_compress_different_levels | ✅ PASSED |
| test_is_worth_compressing_text | ✅ PASSED |
| test_is_worth_compressing_random | ✅ PASSED |
| test_is_worth_compressing_empty | ✅ PASSED |
| test_is_worth_compressing_null_bytes | ✅ PASSED |
| test_is_worth_compressing_small_sample | ✅ PASSED |

Duration: 0.06s

## test_packer.py
PASSED: 15/15
FAILED: none

| Test | Status |
|------|--------|
| test_pack_unpack_single_file | ✅ PASSED |
| test_pack_unpack_multiple_files | ✅ PASSED |
| test_pack_preserves_binary_data | ✅ PASSED |
| test_pack_preserves_filename_with_spaces | ✅ PASSED |
| test_pack_unpack_unicode_filename | ✅ PASSED |
| test_empty_data_file | ✅ PASSED |
| test_pack_many_files | ✅ PASSED |
| test_path_traversal_unix_style | ✅ PASSED |
| test_path_traversal_windows_style | ✅ PASSED |
| test_path_traversal_absolute_unix | ✅ PASSED |
| test_path_traversal_protection | ✅ PASSED |
| test_pack_from_paths_single | ✅ PASSED |
| test_pack_from_paths_multiple | ✅ PASSED |
| test_packed_file_size_property | ✅ PASSED |
| test_packed_file_size_empty | ✅ PASSED |

Duration: 0.09s

## test_crypto.py
PASSED: 14/14
FAILED: none

| Test | Status |
|------|--------|
| test_encrypt_decrypt_roundtrip | ✅ PASSED |
| test_encrypt_decrypt_roundtrip_empty_data | ✅ PASSED |
| test_encrypt_produces_different_ciphertext | ✅ PASSED |
| test_wrong_password_raises | ✅ PASSED |
| test_wrong_password_raises_unicode | ✅ PASSED |
| test_tampered_ciphertext_raises | ✅ PASSED |
| test_tampered_auth_tag_raises | ✅ PASSED |
| test_encrypt_large_data | ✅ PASSED |
| test_checksum_correctness | ✅ PASSED |
| test_checksum_deterministic | ✅ PASSED |
| test_checksum_empty_data | ✅ PASSED |
| test_verify_checksum_pass | ✅ PASSED |
| test_verify_checksum_fail | ✅ PASSED |
| test_verify_checksum_wrong_expected | ✅ PASSED |

Duration: 2.17s

## test_engine.py
PASSED: 16/16
FAILED: none

| Test | Status |
|------|--------|
| test_hide_extract_basic | ✅ PASSED |
| test_hide_extract_with_password | ✅ PASSED |
| test_hide_extract_wrong_password | ✅ PASSED |
| test_hide_extract_no_password_on_encrypted_file | ✅ PASSED |
| test_hide_extract_multi_file | ✅ PASSED |
| test_hide_extract_multi_file_with_password | ✅ PASSED |
| test_hide_empty_payload | ✅ PASSED |
| test_extract_no_payload | ✅ PASSED |
| test_extract_nonexistent_file | ✅ PASSED |
| test_hide_carrier_not_found | ✅ PASSED |
| test_hide_payload_not_found | ✅ PASSED |
| test_carrier_data_preserved | ✅ PASSED |
| test_hide_returns_payload_info_single | ✅ PASSED |
| test_hide_returns_payload_info_encrypted | ✅ PASSED |
| test_hide_returns_payload_info_multi | ✅ PASSED |
| test_hide_extract_compression_disabled | ✅ PASSED |

Duration: 1.30s

## Total
PASSED: 58/58
FAILED: 0

**Kết quả: TẤT CẢ TESTS ĐỀU PASS ✅**
