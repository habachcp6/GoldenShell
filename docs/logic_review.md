# Logic Review — GoldenShell
> Reviewer: Antigravity Debugger Agent  
> Date: 2026-05-20  
> Scope: `engine.py`, `packer.py`, `compressor.py`, `cli.py`, `__main__.py`

---

## Summary

| Bug ID  | Severity | File | Status |
|---------|----------|------|--------|
| BUG-001 | CRITICAL  | `engine.py` | ✅ FIXED |
| BUG-002 | LOW       | `engine.py` | ✅ PASS (by design) |
| BUG-003 | HIGH      | `compressor.py` | ✅ FIXED |
| BUG-004 | HIGH      | `packer.py` | ✅ FIXED |
| BUG-005 | HIGH      | `engine.py` | ✅ FIXED |
| BUG-006 | LOW       | `engine.py` | ✅ PASS (logic correct) |
| BUG-007 | LOW       | `compressor.py` | ✅ PASS (guarded) |
| BUG-008 | HIGH      | `cli.py` | ✅ FIXED |
| BUG-009 | MEDIUM    | `steg_protocol.py` | ℹ️ DESIGN LIMITATION (not fixed) |
| BUG-010 | HIGH      | `packer.py` | ✅ FIXED |
| BUG-011 | LOW       | `__main__.py` | ✅ PASS |

---

## Detailed Findings

### BUG-001 — Empty payload list causes unguarded IndexError
- **File**: `engine.py` → `hide()`, line ~121 (`payload_paths[0]`)
- **Severity**: CRITICAL
- **Root Cause**: `hide()` accepted an empty `payload_paths` list. When `len(payload_paths) == 1` is False (because list is empty), the `else` branch attempted `payload_paths[0]` → `IndexError`. Even if `is_multi` were True for `len > 1`, `pack_from_paths([])` would silently produce a valid 4-byte pack with 0 files, hiding nothing.
- **Trigger**: `engine.hide(carrier, [], output)` or CLI with no payload arguments.
- **Fix Applied**: Added early guard at the top of `hide()`:
  ```python
  if not payload_paths:
      raise GoldenShellError("At least one payload file must be specified.")
  ```
- **Prevention**: Always validate list inputs before indexing.

---

### BUG-002 — Checksum computed on plaintext pre-compress/pre-encrypt
- **File**: `engine.py` → `hide()` line ~125
- **Severity**: LOW (design is actually correct — this is intentional)
- **Analysis**: Checksum is computed on the **raw original payload** before compression and encryption. During extract, checksum is verified **after** decryption and decompression. This is correct: the checksum acts as an integrity seal on the original plaintext. `PASS`.

---

### BUG-003 — `decompress()` leaked raw `zlib.error`; `is_worth_compressing()` on empty data
- **File**: `compressor.py`
- **Severity**: HIGH (two sub-issues)
- **Sub-issue A — decompress() leaked `zlib.error`**:
  - `engine.py` catches `GoldenShellError` subclasses. Raw `zlib.error` bypasses all except chains in `extract()`, surfacing as an "Unexpected error" in the CLI.
  - **Fix**: Wrapped `zlib.decompress()` in try/except and re-raised as `CompressionError` (a new exception class). In `engine.py`, `CompressionError` is caught and re-raised as `IntegrityError`.
- **Sub-issue B — `is_worth_compressing(b"")` logic**:
  - `len(sample) = 0` → used `else 1.0` guard which returned `False`. However, `zlib.compress(b"")` = 8 bytes of overhead → ratio would be `8/0` (guarded) but semantically misleading.
  - **Fix**: Added `if not data: return False` early return. Also simplified the ratio line (no longer needs the conditional `if len(sample) > 0`).

---

### BUG-004 — `unpack_files()` crashes with raw `struct.error` on truncated data
- **File**: `packer.py` → `unpack_files()`
- **Severity**: HIGH
- **Root Cause**: `struct.unpack()` calls were unguarded. Passing truncated or corrupted data (e.g. carrier without proper payload, or tampered file) raised raw `struct.error` which bypassed all GoldenShell exception handlers.
- **Fix Applied**: Wrapped all `struct.unpack` calls inside `try/except struct.error` → re-raised as `PackerError`. `engine.py` catches `PackerError` and re-raises as `IntegrityError`.

---

### BUG-005 — Duplicate filenames in multi-file pack silently overwrite each other
- **File**: `engine.py` → `extract()` multi-file branch
- **Severity**: HIGH
- **Root Cause**: If two packed files share the same name (e.g., hiding `a/report.pdf` and `b/report.pdf`), the second file's `write_bytes()` silently overwrites the first. No warning is given.
- **Fix Applied**: Added deduplication with a counter dictionary:
  ```python
  seen_names: dict[str, int] = {}
  # First occurrence: "report.pdf"
  # Second occurrence: "report_1.pdf"
  # Third occurrence:  "report_2.pdf"
  ```

---

### BUG-006 — Auth tag extraction logic (encrypted path)
- **File**: `engine.py` → `extract()`
- **Severity**: LOW (correct by inspection)
- **Analysis**: `header.payload_size` stores the length of the **ciphertext** (without auth tag, because `encrypt_payload` splits them). Auth tag is read at `file_data[payload_end : payload_end + AUTH_TAG_SIZE]`. This is consistent with how `hide()` writes: `[..., ciphertext, auth_tag, FOOTER_MAGIC]`. Logic is correct. `PASS`.

---

### BUG-007 — Empty file (0 bytes) as payload
- **File**: `compressor.py`, `engine.py`
- **Severity**: LOW (handled correctly)
- **Analysis**: Empty payload (`b""`):
  - `is_worth_compressing(b"")` now returns `False` (after BUG-003 fix) → not compressed.
  - `compute_checksum(b"")` → valid SHA256 of empty bytes.
  - Pack/unpack: packer handles 0-byte data normally.
  - `PASS` after BUG-003 fix.

---

### BUG-008 — CLI does not validate empty payloads list
- **File**: `cli.py` → `hide()` command
- **Severity**: HIGH
- **Root Cause**: `payloads: List[str]` with `typer.Argument` can receive an empty list if no positional args are provided after the carrier. Typer does not enforce a minimum count. The call to `engine_hide(payload_paths=[])` would crash with `IndexError` (pre-BUG-001-fix) or raise `GoldenShellError` (post-fix), but the CLI itself showed no user-friendly message before the engine was invoked.
- **Fix Applied**: Added explicit guard in CLI before engine call:
  ```python
  if not payload_paths:
      console.print("[red]❌ At least one payload file must be specified.[/red]")
      raise typer.Exit(1)
  ```

---

### BUG-009 — MAGIC pattern may appear in carrier data (false positive)
- **File**: `steg_protocol.py` → `find_magic()`
- **Severity**: MEDIUM
- **Analysis**: `MAGIC = b"\x00PHANTOM\xff"` (9 bytes). `find_magic()` uses `data.find(MAGIC, 0)` which returns the **first** occurrence. If the carrier (a PDF, PNG, etc.) happens to contain the byte sequence `\x00PHANTOM\xff`, `find_magic()` returns the wrong position → header parse fails or reads garbage → leads to `struct.error` or checksum mismatch.
- **Current mitigation**: `find_footer()` uses `rfind()` (last occurrence) and the FOOTER_MAGIC is different — so there is an asymmetry. A carrier false-positive would likely cause a `PayloadNotFoundError` or `IntegrityError`, not data corruption.
- **Fix Applied**: **None — this is a known design limitation of binary stacking.** A more robust fix would require searching magic+footer as a pair from the end, or using a longer/more unique magic sequence. This is outside scope of this review session; documented as a known limitation.

---

### BUG-010 — Silent data truncation in `unpack_files()` when `data_len` exceeds remaining bytes
- **File**: `packer.py` → `unpack_files()`
- **Severity**: HIGH
- **Root Cause**: Python byte slicing `data[offset : offset + data_len]` silently returns fewer bytes than `data_len` if `offset + data_len > len(data)`. This means a truncated or tampered pack would produce a `PackedFile` with incomplete data, no error raised, and the checksum would then fail in `engine.py` — but only at checksum verification, not at the point of truncation.
- **Fix Applied**: Added explicit bounds check before each slice:
  ```python
  if offset + data_len > len(data):
      raise PackerError(f"Truncated pack data at entry {i}: ...")
  ```

---

### BUG-011 — `__main__.py` review
- **File**: `__main__.py`
- **Severity**: N/A
- **Analysis**: File is 5 lines. Imports `app` from `goldenshell.cli` and calls `app()`. Correct and minimal. `PASS`.

---

## Edge Case Matrix

| Edge Case | Behavior Before | Behavior After |
|-----------|----------------|----------------|
| `payload_paths = []` | `IndexError` crash | `GoldenShellError`: "At least one payload..." |
| Empty payload file (0 bytes) | Worked, no compression | Correct (PASS) |
| Unicode filename in payload | Works (UTF-8 encode/decode) | PASS |
| Duplicate filenames in multi-file | Second file silently overwrites first | Renamed with `_N` suffix |
| Truncated pack data | Raw `struct.error` or silent truncation | `PackerError` → `IntegrityError` |
| `is_worth_compressing(b"")` | Ratio guard returned `1.0` → False | Returns `False` immediately |
| Corrupted zlib data in decompress | Raw `zlib.error` bypasses CLI handler | `CompressionError` → `IntegrityError` |
| No payload in carrier | `PayloadNotFoundError` (correct) | PASS |
| Wrong password | `DecryptionError` via `InvalidTag` | PASS |

---

## Files Modified

| File | Changes |
|------|---------|
| [`engine.py`](../goldenshell/core/engine.py) | BUG-001 guard; BUG-003 CompressionError import+catch; BUG-004/010 PackerError import+catch; BUG-005 duplicate filename dedup |
| [`packer.py`](../goldenshell/core/packer.py) | BUG-004 struct.error wrapping; BUG-010 bounds validation; new `PackerError` class |
| [`compressor.py`](../goldenshell/core/compressor.py) | BUG-003 `CompressionError` class; `decompress()` wrapping; `is_worth_compressing()` early-return for empty |
| [`cli.py`](../goldenshell/cli.py) | BUG-008 empty payloads guard |
| [`__main__.py`](../goldenshell/__main__.py) | No changes — PASS |
