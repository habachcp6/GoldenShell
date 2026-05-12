# 👻 Phantom — Hide Files Inside Other Files

> **Steganography & Polyglot CLI Tool** — Cross-platform (Windows, Linux, macOS, Docker)

Phantom hides files inside other files using binary stacking technique with AES-256-GCM encryption. The carrier file (PDF, PNG, JPEG, etc.) remains fully functional — it opens normally in any viewer — while secretly containing your hidden payload.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔒 **Hide** | Embed files inside any carrier (PDF, PNG, JPEG, ZIP, MP3, MP4, DOCX...) |
| 📤 **Extract** | Recover hidden files with integrity verification |
| 🔑 **AES-256-GCM** | Military-grade encryption with password protection |
| 📦 **Multi-file** | Hide multiple files in a single carrier |
| 🗜️ **Compression** | Automatic zlib compression to minimize size |
| ✅ **Integrity** | SHA-256 checksum verification |
| 🐳 **Docker** | Run anywhere with Docker |

## 📦 Installation

### pip (Recommended)
```bash
cd phantom
pip install .
```

### Docker
```bash
docker build -t phantom .
docker run -v $(pwd):/workspace phantom hide carrier.pdf secret.txt -o output.pdf
```

## 🚀 Usage

### Hide a file
```bash
# Hide secret.exe inside report.pdf
phantom hide report.pdf secret.exe -o output.pdf

# With encryption
phantom hide report.pdf secret.exe -o output.pdf -p "mypassword"

# Hide multiple files
phantom hide image.png file1.txt file2.zip file3.docx -o steg_image.png -p "pass"
```

### Extract hidden files
```bash
# Extract to directory
phantom extract output.pdf -o ./extracted/

# With password
phantom extract output.pdf -o ./extracted/ -p "mypassword"
```

## 🔧 How It Works

Phantom uses **binary concatenation (stacking)** to append encrypted payload data after the carrier file's valid content. Most file parsers (PDF readers, image viewers, etc.) only read the format-specific portion and ignore trailing data.

```
[Carrier File] + [MAGIC] + [Header] + [Encrypted Payload] + [Footer]
```

The payload goes through: **Compression → Encryption → Embedding**.

## 🛡️ Security

- **AES-256-GCM** encryption with authenticated encryption
- **PBKDF2-HMAC-SHA256** key derivation (600,000 iterations)
- **SHA-256** integrity verification with constant-time comparison
- **Path traversal protection** for extracted filenames

## ⚠️ Disclaimer

This tool is for **educational and authorized security research** purposes only. Do not use for illegal activities.

## 📄 License

MIT License
