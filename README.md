# GoldenShell — Công cụ Steganography

> Giấu file bên trong file khác, có hỗ trợ mã hóa.

GoldenShell cho phép bạn nhúng một hoặc nhiều file bí mật vào bên trong một file bình thường (PDF, PNG, JPEG,...). File gốc vẫn mở và hoạt động bình thường — người khác sẽ không nhận ra có dữ liệu ẩn bên trong.

## Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| **Giấu file** | Nhúng file vào bất kỳ carrier nào (PDF, PNG, JPEG, ZIP, MP3...) |
| **Trích xuất** | Lấy lại file đã giấu, có kiểm tra tính toàn vẹn |
| **Mã hóa** | AES-256-GCM với mật khẩu (tùy chọn) |
| **Nhiều file** | Giấu nhiều file cùng lúc trong một carrier |
| **Nén dữ liệu** | Tự động nén payload để giảm kích thước output |

## Cài đặt

> **Yêu cầu**: Python 3.10 trở lên

**Linux / macOS**
```bash
git clone https://github.com/habachcp6/GoldenShell.git && cd GoldenShell
bash install.sh
```

**Windows**
```bat
git clone https://github.com/habachcp6/GoldenShell.git && cd GoldenShell
install.bat
```

Script cài đặt tự động tạo virtual environment và cài đầy đủ thư viện.

Sau khi cài xong, kích hoạt môi trường và dùng ngay:

```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

goldenshell --help
```

> Nếu không tìm thấy lệnh `goldenshell`, dùng `python -m goldenshell` thay thế.

## Sử dụng

### Giấu file

```bash
# Giấu file không mã hóa
goldenshell hide report.pdf secret.txt -o output.pdf

# Giấu file có mã hóa AES-256-GCM
goldenshell hide report.pdf secret.txt -o output.pdf -p "matkhau"

# Giấu nhiều file cùng lúc
goldenshell hide anh.png file1.txt file2.zip -o output.png -p "matkhau"
```

### Trích xuất file

```bash
# Trích xuất (không mã hóa)
goldenshell extract output.pdf -o ./ketqua/

# Trích xuất (có mã hóa)
goldenshell extract output.pdf -o ./ketqua/ -p "matkhau"
```

## Cách hoạt động

GoldenShell nối dữ liệu ẩn vào sau phần cuối hợp lệ của file carrier. Các trình đọc file (PDF viewer, trình xem ảnh,...) chỉ đọc đến điểm kết thúc theo định dạng của chúng và bỏ qua phần còn lại — đây chính là nơi GoldenShell lưu payload.

Khi giấu file, payload đi qua các bước:

```
File gốc → [Nén zlib] → [Mã hóa AES-256-GCM] → Nhúng vào cuối carrier
```

Khi trích xuất, quá trình diễn ra ngược lại và có kiểm tra SHA-256 để đảm bảo dữ liệu nguyên vẹn.

## Bảo mật

- Mã hóa **AES-256-GCM** (xác thực + mã hóa)
- Dẫn xuất khóa **PBKDF2-HMAC-SHA256** (600.000 vòng lặp)
- Kiểm tra toàn vẹn **SHA-256** bằng so sánh constant-time
- Bảo vệ chống **path traversal** khi giải nén tên file

## Tuyên bố

Công cụ này chỉ dành cho **mục đích học tập và nghiên cứu bảo mật được ủy quyền**. Không sử dụng cho các hoạt động vi phạm pháp luật.

## Giấy phép

MIT License
