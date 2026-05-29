# GoldenShell — Kế hoạch Review & Fix trước khi Push GitHub

**Ngày:** 2026-05-20  
**Mục tiêu:** Kiểm tra toàn bộ mã nguồn, tìm và sửa bugs, đảm bảo project sạch và sẵn sàng publish.

---

## Phân tích ban đầu

GoldenShell là một Python CLI tool steganography sử dụng binary stacking + AES-256-GCM encryption.

**Cấu trúc source:**
```
goldenshell/
  __init__.py        — Package metadata
  __main__.py        — Entry point
  banner.py          — ASCII art
  cli.py             — Typer CLI interface (hide, extract commands)
  core/
    __init__.py
    engine.py        — High-level hide/extract orchestration
    crypto.py        — AES-256-GCM, PBKDF2 key derivation
    steg_protocol.py — Binary header format, magic bytes
    compressor.py    — zlib compression
    packer.py        — Multi-file packing/unpacking
```

---

## Bugs đã phát hiện (sơ bộ — cần confirm)

### 🔴 CRITICAL

**BUG-001** — `engine.py:134-136` — Nonce/salt zero-initialized khi không encrypt  
Dòng `nonce = b"\x00" * 12` và `salt = b"\x00" * 16` được gán trước khi check password.  
Nếu không có password, header sẽ chứa zero nonce/salt (OK về logic, nhưng misleading).  
→ Không phải critical thực sự, cần review thêm.

**BUG-002** — `steg_protocol.py:138-146` — `find_magic()` trả về **vị trí AFTER magic**  
Docstring nói "Returns position after the magic" nhưng caller trong `engine.py:224` lại dùng  
`file_data[magic_pos:]` — tức là bắt đầu từ SAU magic, bỏ qua MAGIC bytes.  
`StegHeader.unpack()` trong `engine.py:225` sẽ parse header trực tiếp — điều này ĐÚNG vì  
header bắt đầu ngay sau MAGIC. Nhưng cần verify hành vi này nhất quán.

**BUG-003** — `engine.py:228` — `header.packed_size()` — Kích thước header bao gồm MAGIC hay không?  
`payload_start = magic_pos + header.packed_size()` — magic_pos đã là vị trí SAU MAGIC,  
nên cộng thêm packed_size() là header size. Điều này có vẻ đúng nhưng cần trace cẩn thận.

### 🟡 MEDIUM

**BUG-004** — `compressor.py:57` — Division by zero risk  
`ratio = len(compressed_sample) / len(sample) if len(sample) > 0 else 1.0`  
Edge case: nếu `data` rỗng (`b""`), `sample` sẽ rỗng, và ratio = 1.0 (không compress) — OK.  
Nhưng `compress(b"")` có thể gây vấn đề ở zlib hay không? Cần test.

**BUG-005** — `engine.py:66` — `PayloadInfo.file_names` dùng mutable default  
`file_names: list[str] = None` với `__post_init__` fix này, nhưng pattern này vẫn cần kiểm tra.

**BUG-006** — `cli.py` — Không có `__main__.py` check hay thiếu?  
`goldenshell/__main__.py` tồn tại nhưng cần kiểm tra nội dung.

### 🟢 INFO / GitHub Readiness

- Thiếu `CHANGELOG.md`
- Thiếu `tests/` directory (không có unit tests)
- Thiếu `CONTRIBUTING.md` hoặc `SECURITY.md`  
- `.gitignore` cần kiểm tra xem có bỏ sót file nào không

---

## Kế hoạch Agent Dispatch

### Phase 2: Parallel Agents (4 agents)

| # | Agent | Focus | Files |
|---|-------|-------|-------|
| 1 | `security-auditor` | Crypto correctness, protocol security | crypto.py, steg_protocol.py, engine.py |
| 2 | `debugger` | Logic bugs, edge cases, flow analysis | engine.py, packer.py, compressor.py |
| 3 | `test-engineer` | Tạo unit tests, verify correctness | Tất cả core files |
| 4 | `devops-engineer` | GitHub readiness: .gitignore, CHANGELOG, missing files | Toàn bộ project |

### Phase 3: Final Review

| # | Agent | Focus |
|---|-------|-------|
| 5 | `quality-inspector` | Final gate: xác nhận tất cả bugs đã sửa, project sẵn sàng |

---

## Acceptance Criteria

- [ ] Không còn logic bug nào trong hide/extract pipeline  
- [ ] Crypto pipeline (encrypt → decrypt) hoạt động chính xác  
- [ ] Edge cases được xử lý (file rỗng, tên file đặc biệt, v.v.)  
- [ ] Unit tests cơ bản được tạo  
- [ ] `.gitignore` đầy đủ  
- [ ] `REVIEW_REPORT.md` được tạo tổng hợp tất cả findings  
- [ ] `python -m goldenshell --help` chạy thành công  
