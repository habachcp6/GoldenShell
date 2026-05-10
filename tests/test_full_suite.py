"""
Comprehensive test suite for Phantom Steganography Tool.
Agent: test-engineer
Tests all features: hide, extract, inspect, info, encryption, multi-file, integrity.
"""

import os
import sys
import hashlib
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from phantom.core.engine import hide, extract, inspect, info
from phantom.core.engine import PayloadNotFoundError, DecryptionError, IntegrityError
from phantom.core.crypto import encrypt_payload, decrypt_payload, compute_checksum, verify_checksum
from phantom.core.compressor import compress, decompress, is_worth_compressing
from phantom.core.packer import PackedFile, pack_files, unpack_files
from phantom.core.steg_protocol import StegHeader, StegFlags, MAGIC, FOOTER_MAGIC, find_footer, find_magic


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  [PASS] {name}")

    def fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  [FAIL] {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"  RESULTS: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print(f"\n  FAILURES:")
            for name, reason in self.errors:
                print(f"    - {name}: {reason}")
        print(f"{'='*60}")
        return self.failed == 0


def run_all_tests():
    result = TestResult()
    tmp = tempfile.mkdtemp(prefix="phantom_test_")

    try:
        # ============================================================
        # AGENT: test-engineer — Module Tests
        # ============================================================
        print("\n[TEST GROUP 1] Crypto Module")

        # Test 1: Encrypt/Decrypt roundtrip
        try:
            data = b"Hello Phantom! This is secret data." * 100
            ct, nonce, salt, tag = encrypt_payload(data, "testpass123")
            decrypted = decrypt_payload(ct, nonce, salt, tag, "testpass123")
            assert decrypted == data, "Decrypted data mismatch"
            result.ok("crypto_encrypt_decrypt_roundtrip")
        except Exception as e:
            result.fail("crypto_encrypt_decrypt_roundtrip", str(e))

        # Test 2: Wrong password fails
        try:
            data = b"Secret data for wrong password test"
            ct, nonce, salt, tag = encrypt_payload(data, "correctpass")
            try:
                decrypt_payload(ct, nonce, salt, tag, "wrongpass")
                result.fail("crypto_wrong_password_rejected", "Should have raised error")
            except Exception:
                result.ok("crypto_wrong_password_rejected")
        except Exception as e:
            result.fail("crypto_wrong_password_rejected", str(e))

        # Test 3: Checksum
        try:
            data = b"Checksum test data"
            cs = compute_checksum(data)
            assert verify_checksum(data, cs), "Checksum should match"
            assert not verify_checksum(b"different data", cs), "Checksum should not match"
            result.ok("crypto_checksum_verify")
        except Exception as e:
            result.fail("crypto_checksum_verify", str(e))

        # ============================================================
        print("\n[TEST GROUP 2] Compression Module")

        # Test 4: Compress/decompress roundtrip
        try:
            data = b"AAAA" * 10000  # Highly compressible
            compressed = compress(data)
            decompressed = decompress(compressed)
            assert decompressed == data, "Decompressed data mismatch"
            assert len(compressed) < len(data), "Compression should reduce size"
            result.ok("compress_decompress_roundtrip")
        except Exception as e:
            result.fail("compress_decompress_roundtrip", str(e))

        # Test 5: is_worth_compressing
        try:
            compressible = b"AAAA" * 10000
            assert is_worth_compressing(compressible), "Should be worth compressing"
            result.ok("compress_worth_check")
        except Exception as e:
            result.fail("compress_worth_check", str(e))

        # ============================================================
        print("\n[TEST GROUP 3] Packer Module")

        # Test 6: Pack/unpack roundtrip
        try:
            files = [
                PackedFile("file1.txt", b"Content of file 1"),
                PackedFile("file2.bin", b"\x00\x01\x02\x03" * 100),
                PackedFile("file3.py", b"print('hello world')"),
            ]
            packed = pack_files(files)
            unpacked = unpack_files(packed)
            assert len(unpacked) == 3, f"Expected 3 files, got {len(unpacked)}"
            for orig, restored in zip(files, unpacked):
                assert orig.filename == restored.filename, f"Filename mismatch: {orig.filename} vs {restored.filename}"
                assert orig.data == restored.data, f"Data mismatch for {orig.filename}"
            result.ok("packer_multi_file_roundtrip")
        except Exception as e:
            result.fail("packer_multi_file_roundtrip", str(e))

        # ============================================================
        print("\n[TEST GROUP 4] Protocol Module")

        # Test 7: Header pack/unpack
        try:
            header = StegHeader(
                flags=int(StegFlags.ENCRYPTED | StegFlags.COMPRESSED),
                nonce=b"\x01" * 12,
                salt=b"\x02" * 16,
                filename="test_payload.exe",
                payload_size=12345,
                checksum=b"\x03" * 32,
            )
            packed = header.pack()
            restored = StegHeader.unpack(packed)
            assert restored.filename == "test_payload.exe"
            assert restored.payload_size == 12345
            assert restored.is_encrypted == True
            assert restored.is_compressed == True
            assert restored.nonce == b"\x01" * 12
            assert restored.salt == b"\x02" * 16
            result.ok("protocol_header_pack_unpack")
        except Exception as e:
            result.fail("protocol_header_pack_unpack", str(e))

        # Test 8: Magic/footer detection
        try:
            data = b"some carrier data" + MAGIC + b"header" + FOOTER_MAGIC
            assert find_footer(data) is not None, "Footer should be found"
            assert find_magic(data) is not None, "Magic should be found"

            clean = b"just normal data without any magic"
            assert find_footer(clean) is None, "Footer should not be found in clean data"
            assert find_magic(clean) is None, "Magic should not be found in clean data"
            result.ok("protocol_magic_footer_detection")
        except Exception as e:
            result.fail("protocol_magic_footer_detection", str(e))

        # ============================================================
        print("\n[TEST GROUP 5] Engine — Full Integration (hide/extract)")

        # Create test files
        carrier_path = Path(tmp) / "carrier.pdf"
        carrier_path.write_bytes(b"%PDF-1.4 Fake PDF carrier content for testing " * 10)

        payload_path = Path(tmp) / "secret.txt"
        payload_path.write_bytes(b"This is TOP SECRET data hidden by Phantom!")

        # Test 9: Hide + Extract (no encryption)
        try:
            output_path = Path(tmp) / "steg_output.pdf"
            extract_dir = Path(tmp) / "extracted_no_enc"

            hide(carrier_path, [payload_path], output_path)
            extracted = extract(output_path, extract_dir)

            assert len(extracted) == 1
            assert extracted[0].name == "secret.txt"
            assert extracted[0].read_bytes() == payload_path.read_bytes()
            result.ok("engine_hide_extract_no_encryption")
        except Exception as e:
            result.fail("engine_hide_extract_no_encryption", str(e))

        # Test 10: Hide + Extract (with encryption)
        try:
            output_enc = Path(tmp) / "steg_encrypted.pdf"
            extract_dir_enc = Path(tmp) / "extracted_enc"

            hide(carrier_path, [payload_path], output_enc, password="S3cur3P@ss!")
            extracted = extract(output_enc, extract_dir_enc, password="S3cur3P@ss!")

            assert len(extracted) == 1
            assert extracted[0].read_bytes() == payload_path.read_bytes()
            result.ok("engine_hide_extract_with_encryption")
        except Exception as e:
            result.fail("engine_hide_extract_with_encryption", str(e))

        # Test 11: Wrong password rejection
        try:
            try:
                extract(output_enc, Path(tmp) / "should_fail", password="BadPassword")
                result.fail("engine_wrong_password_rejected", "Should have raised DecryptionError")
            except DecryptionError:
                result.ok("engine_wrong_password_rejected")
        except Exception as e:
            result.fail("engine_wrong_password_rejected", str(e))

        # Test 12: Inspect (has payload)
        try:
            assert inspect(output_path) == True, "Should detect payload"
            result.ok("engine_inspect_has_payload")
        except Exception as e:
            result.fail("engine_inspect_has_payload", str(e))

        # Test 13: Inspect (clean file)
        try:
            assert inspect(carrier_path) == False, "Should not detect payload in clean file"
            result.ok("engine_inspect_clean_file")
        except Exception as e:
            result.fail("engine_inspect_clean_file", str(e))

        # Test 14: Info
        try:
            payload_info = info(output_enc)
            assert payload_info is not None
            assert payload_info.is_encrypted == True
            assert payload_info.filename == "secret.txt"
            assert payload_info.version == 1
            result.ok("engine_info_metadata")
        except Exception as e:
            result.fail("engine_info_metadata", str(e))

        # Test 15: Info on clean file
        try:
            clean_info = info(carrier_path)
            assert clean_info is None, "Should return None for clean file"
            result.ok("engine_info_clean_file_returns_none")
        except Exception as e:
            result.fail("engine_info_clean_file_returns_none", str(e))

        # ============================================================
        print("\n[TEST GROUP 6] Engine — Malware Payload Test")

        # Test 16: Hide real malware script
        try:
            malware_path = Path("d:/CTF-test/phantom/test_malware.py")
            if malware_path.exists():
                output_malware = Path(tmp) / "innocent_report.pdf"
                extract_malware = Path(tmp) / "extracted_malware"

                result_info = hide(
                    carrier_path, [malware_path], output_malware,
                    password="M@lw4r3T3st!"
                )

                assert result_info.is_encrypted == True
                assert result_info.filename == "test_malware.py"

                # Carrier should still be "readable" (starts with original content)
                output_data = output_malware.read_bytes()
                assert output_data[:5] == b"%PDF-", "Output should still start like a PDF"

                # Extract and verify
                extracted = extract(output_malware, extract_malware, password="M@lw4r3T3st!")
                assert len(extracted) == 1
                assert extracted[0].name == "test_malware.py"

                # SHA-256 integrity check
                original_hash = hashlib.sha256(malware_path.read_bytes()).hexdigest()
                extracted_hash = hashlib.sha256(extracted[0].read_bytes()).hexdigest()
                assert original_hash == extracted_hash, f"Hash mismatch: {original_hash} vs {extracted_hash}"

                result.ok("engine_malware_hide_extract_integrity")
            else:
                result.fail("engine_malware_hide_extract_integrity", "test_malware.py not found")
        except Exception as e:
            result.fail("engine_malware_hide_extract_integrity", str(e))

        # ============================================================
        print("\n[TEST GROUP 7] Engine — Multi-file Test")

        # Test 17: Hide multiple files
        try:
            file_a = Path(tmp) / "file_a.txt"
            file_b = Path(tmp) / "file_b.bin"
            file_c = Path(tmp) / "file_c.py"
            file_a.write_bytes(b"File A content - text data")
            file_b.write_bytes(os.urandom(256))  # Random binary
            file_c.write_bytes(b"print('File C - Python script')")

            output_multi = Path(tmp) / "multi_steg.pdf"
            extract_multi = Path(tmp) / "extracted_multi"

            hide(carrier_path, [file_a, file_b, file_c], output_multi, password="multi123")
            extracted = extract(output_multi, extract_multi, password="multi123")

            assert len(extracted) == 3, f"Expected 3 files, got {len(extracted)}"

            # Verify each file
            for orig_path in [file_a, file_b, file_c]:
                matching = [f for f in extracted if f.name == orig_path.name]
                assert len(matching) == 1, f"Missing file: {orig_path.name}"
                assert matching[0].read_bytes() == orig_path.read_bytes(), f"Content mismatch: {orig_path.name}"

            result.ok("engine_multi_file_hide_extract")
        except Exception as e:
            result.fail("engine_multi_file_hide_extract", str(e))

        # ============================================================
        print("\n[TEST GROUP 8] Engine — Edge Cases")

        # Test 18: Empty file as payload
        try:
            empty_file = Path(tmp) / "empty.txt"
            empty_file.write_bytes(b"")
            output_empty = Path(tmp) / "steg_empty.pdf"
            extract_empty = Path(tmp) / "extracted_empty"

            hide(carrier_path, [empty_file], output_empty)
            extracted = extract(output_empty, extract_empty)
            assert len(extracted) == 1
            assert extracted[0].read_bytes() == b""
            result.ok("engine_empty_payload")
        except Exception as e:
            result.fail("engine_empty_payload", str(e))

        # Test 19: Large payload
        try:
            large_file = Path(tmp) / "large.bin"
            large_data = os.urandom(1024 * 1024)  # 1MB random data
            large_file.write_bytes(large_data)

            output_large = Path(tmp) / "steg_large.pdf"
            extract_large = Path(tmp) / "extracted_large"

            hide(carrier_path, [large_file], output_large, password="large!")
            extracted = extract(output_large, extract_large, password="large!")

            assert extracted[0].read_bytes() == large_data
            result.ok("engine_large_payload_1mb")
        except Exception as e:
            result.fail("engine_large_payload_1mb", str(e))

        # Test 20: No-compress option
        try:
            output_nocomp = Path(tmp) / "steg_nocomp.pdf"
            extract_nocomp = Path(tmp) / "extracted_nocomp"

            result_info = hide(carrier_path, [payload_path], output_nocomp, compress_payload=False)
            assert result_info.is_compressed == False, "Should not be compressed"

            extracted = extract(output_nocomp, extract_nocomp)
            assert extracted[0].read_bytes() == payload_path.read_bytes()
            result.ok("engine_no_compress_option")
        except Exception as e:
            result.fail("engine_no_compress_option", str(e))

    finally:
        # Cleanup
        shutil.rmtree(tmp, ignore_errors=True)

    return result.summary()


if __name__ == "__main__":
    print("=" * 60)
    print("  PHANTOM TEST SUITE — Agent: test-engineer")
    print("=" * 60)

    success = run_all_tests()
    sys.exit(0 if success else 1)
