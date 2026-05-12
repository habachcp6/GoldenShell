# 🐚 GoldenShell — Hide Files Inside Other Files

> **Steganography & Polyglot CLI Tool** — Cross-platform (Windows, Linux, macOS, Docker)

GoldenShell hides files inside other files using binary stacking technique with AES-256-GCM encryption. The carrier file (PDF, PNG, JPEG, etc.) remains fully functional — it opens normally in any viewer — while secretly containing your hidden payload.

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

> **Requires**: Python 3.10+

### pip (Recommended — use a virtual environment)
```bash
git clone https://github.com/habachcp6/GoldenShell.git
cd GoldenShell
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate
pip install .
```

After activating the virtual environment, the `goldenshell` command will be available directly.

### Alternative (without venv)
```bash
pip install .
# Use python -m phantom if goldenshell is not in PATH:
python -m phantom --help
```

### Docker
```bash
docker build -t goldenshell .
docker run -v $(pwd):/workspace goldenshell hide carrier.pdf secret.txt -o output.pdf
```

## 🚀 Usage

### Hide a file
```bash
# Hide secret.exe inside report.pdf
goldenshell hide report.pdf secret.exe -o output.pdf

# With encryption
goldenshell hide report.pdf secret.exe -o output.pdf -p "mypassword"

# Hide multiple files
goldenshell hide image.png file1.txt file2.zip file3.docx -o steg_image.png -p "pass"
```

### Extract hidden files
```bash
# Extract to directory
goldenshell extract output.pdf -o ./extracted/

# With password
goldenshell extract output.pdf -o ./extracted/ -p "mypassword"
```

> **Tip**: If `goldenshell` is not found, use `python -m phantom` instead.

## 🔧 How It Works

GoldenShell uses **binary concatenation (stacking)** to append encrypted payload data after the carrier file's valid content. Most file parsers (PDF readers, image viewers, etc.) only read the format-specific portion and ignore trailing data.

```
[Carrier File] + [MAGIC] + [Header] + [Encrypted Payload] + [Footer]
```

The payload goes through: **Compression → Encryption → Embedding**.

## 🛡️ Security

- **AES-256-GCM** encryption with authenticated encryption
- **PBKDF2-HMAC-SHA256** key derivation (600,000 iterations)
- **SHA-256** integrity verification with constant-time comparison
- **Path traversal protection** for extracted filenames

## 🧪 Running Tests

```bash
python tests/test_full_suite.py
```

## ⚠️ Disclaimer

This tool is for **educational and authorized security research** purposes only. Do not use for illegal activities.

## 📄 License

MIT License
