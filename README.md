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

```bash
git clone https://github.com/habachcp6/GoldenShell.git
cd GoldenShell
pip install .
```

Sau khi cài xong, dùng ngay:

```bash
goldenshell --help
```

> Nếu không tìm thấy lệnh `goldenshell`, dùng `python -m goldenshell` thay thế.


## Sử dụng

### Giấu file — Không mã hóa

```bash
goldenshell hide secret.txt -c report.pdf
```

Output tự tạo tên: `report_hidden.pdf`

---

### Giấu file — Có mã hóa AES-256-GCM

```bash
goldenshell hide secret.txt -c report.pdf -p "matkhau"
```

---

### Chỉ định tên output thủ công

```bash
goldenshell hide secret.txt -c report.pdf -o output.pdf -p "matkhau"
```

---

### Giấu nhiều file cùng lúc

```bash
goldenshell hide file1.txt file2.zip file3.docx -c anh.png -p "matkhau"
```

---

### Dùng đường dẫn từ thư mục khác

```bash
# Windows
goldenshell hide "D:\secrets\data.zip" -c "C:\docs\report.pdf" -o "C:\out\output.pdf"

# Linux/macOS
goldenshell hide /mnt/data/secret.zip -c /home/user/docs/report.pdf
```

---

### Tắt nén (với file đã nén sẵn như ZIP, MP4)

```bash
goldenshell hide archive.zip -c anh.png --no-compress
```

---

### Trích xuất file — Không mã hóa

```bash
goldenshell extract output.pdf -o ./ketqua/
```

### Trích xuất file — Có mã hóa

```bash
goldenshell extract output.pdf -o ./ketqua/ -p "matkhau"
```



## Cách hoạt động

GoldenShell nối dữ liệu ẩn vào sau phần cuối hợp lệ của file carrier. Các trình đọc file (PDF viewer, trình xem ảnh,...) chỉ đọc đến điểm kết thúc theo định dạng của chúng và bỏ qua phần còn lại — đây chính là nơi GoldenShell lưu payload.

Khi giấu file, payload đi qua các bước:

```
File gốc → [Nén zlib] → [Mã hóa AES-256-GCM] → Nhúng vào cuối carrier
```

Khi trích xuất, quá trình diễn ra ngược lại và có kiểm tra SHA-256 để đảm bảo dữ liệu nguyên vẹn.



## Tuyên bố

Công cụ này chỉ dành cho **mục đích học tập và nghiên cứu bảo mật được ủy quyền**. Không sử dụng cho các hoạt động vi phạm pháp luật.

## Giấy phép

MIT License
