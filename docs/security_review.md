# GoldenShell — Security Review Report

**Reviewer**: Antigravity Security Auditor  
**Date**: 2026-05-20  
**Scope**: `crypto.py`, `steg_protocol.py`, `engine.py` (crypto-related sections)  
**Protocol version audited**: 1

---

## Summary

| Severity | Count | Fixed? |
|----------|-------|--------|
| CRITICAL | 0 | — |
| HIGH | 2 | ✅ Yes |
| MEDIUM | 2 | ✅ Yes |
| LOW | 2 | ⚠️ Advisory only |
| PASS | 5 | — |

---

## Findings

---

### [HIGH-001] Path Traversal — single-file extraction

- **File**: `engine.py`, line 274 (original)
- **Description**: `header.filename` from the embedded header is used directly as the output path:
  ```python
  out_path = output_dir / header.filename
  ```
  A maliciously crafted steg file could set `filename = "../../../etc/cron.d/backdoor"`, causing the extracted file to be written outside the intended `output_dir`.
- **Fix applied**: Sanitize with `Path(header.filename).name` which strips all directory components, keeping only the basename. Fallback to `"extracted_payload"` if the result is empty or a dot-only path.
- **Status**: ✅ FIXED in `engine.py`

---

### [HIGH-002] Path Traversal — multi-file extraction

- **File**: `engine.py`, lines 279–295 (original)
- **Description**: Same issue as HIGH-001 but for the multi-file code path. `pf.filename` from packed files was used without sanitization:
  ```python
  base_name = pf.filename
  out_path = output_dir / deduped_name
  ```
- **Fix applied**: Added `Path(pf.filename).name` sanitization before the deduplication logic, with the same fallback.
- **Status**: ✅ FIXED in `engine.py`

---

### [MEDIUM-001] Missing `fname_len` bounds validation — Header parse

- **File**: `steg_protocol.py`, `StegHeader.unpack()` (original line 94–121)
- **Description**: `fname_len` is a 16-bit unsigned integer from network bytes (max 65535). Without validation, a tampered header could set `fname_len` to a value that extends the filename slice into payload bytes, producing a garbage filename or silently miscalculating `offset`, which then corrupts the `payload_size` and `checksum` reads that follow.
- **Fix applied**: Two guards added before the filename slice:
  1. Check `len(data) >= HEADER_FIXED_SIZE` upfront.
  2. Check `offset + fname_len + PAYLOAD_META_SIZE <= len(data)` before slicing.
- **Status**: ✅ FIXED in `steg_protocol.py`

---

### [MEDIUM-002] Missing `payload_size` bounds validation — payload extraction

- **File**: `engine.py`, lines 228–237 (original)
- **Description**: `header.payload_size` is read directly from the (unprotected) header and used to slice `file_data`:
  ```python
  raw_payload = file_data[payload_start:payload_end]
  ```
  An attacker that tampers the non-encrypted header can set `payload_size` to an arbitrary value. Python silent-truncates out-of-range slices, so this doesn't crash but causes wrong data to be fed into decrypt/decompress/checksum, leading to confusing errors (or, in some edge cases, integrity bypass by shortening the read).

  Additionally, for encrypted payloads, the auth_tag read `file_data[payload_end : payload_end + AUTH_TAG_SIZE]` was not length-checked — it could silently return fewer than 16 bytes.
- **Fix applied**:
  1. Added check: `payload_size < 0 or payload_start + payload_size > len(file_data)` → raise `PayloadNotFoundError`.
  2. Added check: `len(auth_tag) != AUTH_TAG_SIZE` → raise `PayloadNotFoundError`.
- **Status**: ✅ FIXED in `engine.py`

---

### [LOW-001] `InvalidTag` imported inside `try` block

- **File**: `engine.py`, line 244 (original)
- **Description**: `from cryptography.exceptions import InvalidTag` was placed inside the `try` block, immediately above the line that could raise it. If the import itself failed (e.g., wrong `cryptography` version), `NameError` would be raised instead of a clean error, and the `except InvalidTag` clause would never match.
- **Fix applied**: Moved to top-level imports (line 28 in revised file), alongside other `cryptography` imports.
- **Status**: ✅ FIXED in `engine.py`

---

### [LOW-002] Unauthenticated header + SHA-256 checksum provides no integrity against active attackers (unencrypted mode)

- **File**: `engine.py`, `steg_protocol.py`
- **Description**: When no password is provided, the protocol uses no cryptographic authentication. The checksum stored in the header is a bare SHA-256 digest — an attacker who can modify the file can recompute and patch the checksum too. This means:
  - In **encrypted** mode: AES-GCM auth tag + PBKDF2 key binding protects the payload. Tampering the header causes decrypt to fail (wrong nonce/salt → bad key → `InvalidTag`).
  - In **unencrypted** mode: There is **no binding** between the checksum and any secret. Any attacker with write access to the file can modify payload AND update the checksum → integrity check passes.
- **Recommendation**: Consider adding an optional HMAC-SHA256 over the full payload (keyed with a user-supplied integrity password, distinct from encryption password), or warn users clearly that unencrypted mode does not protect against active tampering.
- **Fix applied**: None (requires protocol change and user-facing decision). Advisory note only.
- **Status**: ⚠️ ADVISORY — No fix applied, design-level limitation documented

---

## PASS Items (no issues found)

### [PASS-001] AES-256-GCM usage — `crypto.py`

AESGCM from `cryptography` (backed by OpenSSL) provides authenticated encryption. Nonce is 12 bytes (96-bit, optimal for GCM). Auth tag is 16 bytes (128-bit). Ciphertext is correctly separated from tag and stored separately in the protocol stream. Reconstitution (`ciphertext + auth_tag`) before `AESGCM.decrypt()` is correct.

### [PASS-002] PBKDF2-HMAC-SHA256 key derivation — `crypto.py`

`KDF_ITERATIONS = 600_000` meets the OWASP 2023 recommendation for PBKDF2-HMAC-SHA256. Salt is 16 bytes (128-bit), generated via `os.urandom`. Key is 32 bytes (256-bit). No reuse of nonce/salt (both freshly generated per encryption).

### [PASS-003] `find_magic()` → `header_data = file_data[magic_pos:]` — flow correctness

`find_magic()` returns `idx + len(MAGIC)` — i.e., the first byte **after** the magic sequence. `header_data = file_data[magic_pos:]` therefore starts at the first byte of the header, which is exactly what `StegHeader.unpack()` expects. `payload_start = magic_pos + header.packed_size()` correctly points to the first byte of payload data. **Flow is correct** ✅

### [PASS-004] Auth tag placement consistency between hide and extract — `engine.py`

**Hide side**: `encrypt_payload` returns `(ciphertext, nonce, salt, auth_tag)`. `header.payload_size = len(ciphertext)` (without tag). Output layout: `[carrier][MAGIC][header][ciphertext][auth_tag][FOOTER_MAGIC]`.

**Extract side**: `payload_end = payload_start + header.payload_size` → `raw_payload = file_data[payload_start:payload_end]` (ciphertext only). `auth_tag = file_data[payload_end : payload_end + AUTH_TAG_SIZE]` (next 16 bytes). Reconstituted as `ciphertext + auth_tag` for `AESGCM.decrypt()`. **Perfectly consistent** ✅

### [PASS-005] Timing-safe checksum comparison — `crypto.py`

`verify_checksum()` uses `hmac.compare_digest()` for constant-time comparison, preventing timing side-channel attacks. ✅

---

## Crypto/Protocol Flow Summary

```
HIDE:
  raw_payload
    → [compute_checksum(raw_payload)]        ← checksum of ORIGINAL plaintext
    → [compress if beneficial]
    → [encrypt_payload → ciphertext + auth_tag]
    → header(nonce, salt, payload_size=len(ciphertext), checksum)
    → output: [carrier][MAGIC][header][ciphertext][auth_tag?][FOOTER]

EXTRACT:
  file_data
    → find_footer() + find_magic()
    → StegHeader.unpack(file_data[magic_pos:])
    → raw_payload = file_data[payload_start : payload_start + header.payload_size]
    → auth_tag = file_data[payload_end : payload_end + 16]   (if encrypted)
    → decrypt_payload(raw_payload, nonce, salt, auth_tag, password)
    → decompress()
    → verify_checksum(raw_payload, header.checksum)          ← verify ORIGINAL plaintext
    → write files
```

Checksum is computed on the **pre-compress, pre-encrypt** plaintext and verified on the **post-decrypt, post-decompress** plaintext. This is semantically correct — it verifies end-to-end data fidelity.

---

*Report generated by Antigravity Security Auditor — GoldenShell v1 protocol review.*
