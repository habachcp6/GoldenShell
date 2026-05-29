# 🧪 TEST REPORT — GoldenShell v1.0.0

> Ngày kiểm thử: 2026-05-29  
> Phiên bản: `main` commit `db15541`  
> Môi trường: Linux (Kali 2024, Python 3.13) + Windows 11 (Python 3.x)

---

## Tóm tắt

| Platform | Pass | Fail | Tổng |
|----------|------|------|------|
| 🐧 Linux (Kali) | **30** | **0** | 30 |
| 🪟 Windows | TBD | TBD | 30 |

---

## 🐛 Bugs Đã Phát hiện & Đã Fix

### BUG-CRITICAL: Protocol `find_magic()` dùng sai chiều tìm kiếm

| Thuộc tính | Giá trị |
|-----------|---------|
| **Severity** | 🔴 Critical (Security) |
| **File** | `goldenshell/core/steg_protocol.py` |
| **Triệu chứng** | Khi carrier đã chứa payload (nested steg), `extract` đọc payload cũ (không mã hóa) thay vì payload mới (mã hóa). Wrong password và no-password đều extract thành công. |
| **Root Cause** | `find_magic()` dùng `data.find()` tìm FIRST magic, nhưng `find_footer()` dùng `data.rfind()` tìm LAST footer → mismatch khi có nhiều cặp MAGIC/FOOTER |
| **Fix** | `find_magic()` nay tìm LAST magic trước LAST footer (dùng `rfind` trên slice `data[:footer_pos]`) |
| **Commit** | `db15541` |
| **Status** | ✅ Fixed & Verified |

### BUG-PATH: `goldenshell: command not found` sau `bash install.sh`

| Thuộc tính | Giá trị |
|-----------|---------|
| **Severity** | 🟡 High (UX Breaking) |
| **File** | `install.sh` |
| **Triệu chứng** | Sau cài đặt thành công, gõ `goldenshell` vẫn báo `command not found` |
| **Root Cause** | `pip install . --break-system-packages` cài binary vào `~/.local/bin` nhưng thư mục này không có trong PATH mặc định của Kali |
| **Fix** | `install.sh` nay detect binary location sau khi cài, tự thêm vào PATH của session hiện tại VÀ ghi vào `~/.bashrc`/`~/.zshrc` |
| **Commit** | `5de2d44` |
| **Status** | ✅ Fixed & Verified |

---

## 📋 Kết quả Chi tiết — Linux (Kali 2024, Python 3.13)

### Group A: Installation

| ID | Test Case | Kết quả | Ghi chú |
|----|-----------|---------|---------|
| A1 | Clone từ GitHub | ✅ PASS | `git clone` thành công |
| A2 | `bash install.sh` | ✅ PASS | `Installation complete!` |
| A3 | `goldenshell` trong PATH | ✅ PASS | Binary truy cập được sau install |
| A4 | `python3 -m goldenshell --help` | ✅ PASS | Module mode hoạt động |
| A5 | `pip install . --break-system-packages` | ✅ PASS | Exit 0 |
| A6 | Reinstall (cài đè) | ✅ PASS | Không lỗi |

### Group B: Help/CLI

| ID | Test Case | Kết quả | Ghi chú |
|----|-----------|---------|---------|
| B1 | `goldenshell --help` | ✅ PASS | Hiện mô tả tiếng Việt |
| B2 | `goldenshell hide --help` có `-c` | ✅ PASS | Option carrier hiển thị |
| B3 | `goldenshell extract --help` tiếng Việt | ✅ PASS | Help text tiếng Việt |
| B4 | Không tham số → banner | ✅ PASS | Banner ASCII art hiện |

### Group C: Hide

| ID | Test Case | Kết quả | Ghi chú |
|----|-----------|---------|---------|
| C1 | Hide 1 file, không mã hóa | ✅ PASS | Auto output = tên carrier |
| C2 | Hide 1 file + password AES-256 | ✅ PASS | AES-256-GCM xác nhận |
| C3 | Hide với output thủ công | ✅ PASS | |
| C4 | Hide nhiều file (multi) | ✅ PASS | `Files: 2` |
| C5 | Hide nhiều file + password | ✅ PASS | |
| C6 | `--no-compress` flag | ✅ PASS | `Compressed: No` |
| C7 | Output giữ nguyên tên carrier | ✅ PASS | |
| C8 | File lớn 2MB | ✅ PASS | Hoàn thành bình thường |

### Group D: Extract

| ID | Test Case | Kết quả | Ghi chú |
|----|-----------|---------|---------|
| D1 | Extract không mã hóa | ✅ PASS | |
| D2 | Extract đúng mật khẩu | ✅ PASS | |
| D3 | Extract sai mật khẩu → lỗi | ✅ PASS | `Decryption failed` (sau fix BUG-CRITICAL) |
| D4 | Extract multi-file | ✅ PASS | 2 files extracted |
| D5 | SHA-256 nguyên vẹn | ✅ PASS | Hash gốc = hash extracted |
| D6 | Encrypted file không có password → lỗi | ✅ PASS | `Password required` (sau fix BUG-CRITICAL) |

### Group E: Error Handling

| ID | Test Case | Kết quả | Ghi chú |
|----|-----------|---------|---------|
| E1 | Carrier không tồn tại | ✅ PASS | "Không tìm thấy file carrier" |
| E2 | Payload không tồn tại | ✅ PASS | "Không tìm thấy file payload" |
| E3 | File không chứa payload | ✅ PASS | Báo lỗi đúng |
| E4 | Thiếu flag `-c` bắt buộc | ✅ PASS | Typer báo missing option |

### Group F: Edge Cases

| ID | Test Case | Kết quả | Ghi chú |
|----|-----------|---------|---------|
| F1 | Tên file có khoảng trắng | ✅ PASS | Quote hoạt động đúng |
| F2 | Đường dẫn tuyệt đối | ✅ PASS | |

---

## 📋 Kết quả Chi tiết — Windows 11

> *(Đang cập nhật...)*

---

## 🔧 Commits Trong Phiên Kiểm thử Này

| Commit | Mô tả |
|--------|-------|
| `5de2d44` | fix: install.sh detect binary path + add to PATH in session & bashrc/zshrc |
| `db15541` | fix: find_magic searches backwards from last footer (critical security bug) |
