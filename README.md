# GoldenShell — Hide Files Inside Other Files

> **Steganography & Polyglot CLI Tool** — Cross-platform (Windows, Linux, macOS, Docker)

GoldenShell hides files inside other files using binary stacking technique with AES-256-GCM encryption. The carrier file (PDF, PNG, JPEG, etc.) remains fully functional — it opens normally in any viewer — while secretly containing your hidden payload.

## Features

| Feature | Description |
|---------|-------------|
| **Hide** | Embed files inside any carrier (PDF, PNG, JPEG, ZIP, MP3, MP4, DOCX...) |
| **Extract** | Recover hidden files with integrity verification |
| **AES-256-GCM** | Military-grade encryption with password protection |
| **Multi-file** | Hide multiple files in a single carrier |
| **Compression** | Automatic zlib compression to minimize size |
| **Integrity** | SHA-256 checksum verification |
| **Docker** | Run anywhere with Docker |

## Installation

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
# Use python -m goldenshell if goldenshell is not in PATH:
python -m goldenshell --help
```

### Docker
```bash
docker build -t goldenshell .
docker run -v $(pwd):/workspace goldenshell hide carrier.pdf secret.txt -o output.pdf
```

## Usage

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

> **Tip**: If `goldenshell` is not found, use `python -m goldenshell` instead.

## How It Works

GoldenShell uses **binary concatenation (stacking)** — a polyglot technique that appends data after the end of a carrier file's valid content. Most file format parsers (PDF readers, image viewers, media players) only read up to their format-specific EOF marker and ignore any trailing bytes. GoldenShell exploits this behavior to embed hidden payloads invisibly.

### Processing Pipeline

When hiding a file, the payload goes through three stages:

```
[Original Payload]
        |
        v
  1. COMPRESSION (zlib)
     - Only applied if compression reduces size by >= 10%
     - Tested on a 4KB sample before applying to full payload
     - Reduces final output size for compressible data (text, code, documents)
        |
        v
  2. ENCRYPTION (AES-256-GCM)
     - Password-based: PBKDF2-HMAC-SHA256 derives a 256-bit key
     - 600,000 KDF iterations (OWASP 2023 recommendation)
     - Random 12-byte nonce + 16-byte salt per operation
     - Produces ciphertext + 16-byte authentication tag
     - Skipped if no password is provided
        |
        v
  3. EMBEDDING (Binary Stacking)
     - Appended after carrier file's original content
```

### Binary Format

The final output file has this structure:

```
+------------------------------------------+
| Original Carrier File Data               |  (unchanged — file opens normally)
+------------------------------------------+
| MAGIC: \x00PHANTOM\xff  (9 bytes)        |  (identifies GoldenShell payload)
+------------------------------------------+
| HEADER (variable size):                  |
|   - version     (1 byte)                |
|   - flags       (1 byte)  [enc/comp/multi]|
|   - nonce       (12 bytes)               |
|   - salt        (16 bytes)               |
|   - filename    (variable length)        |
|   - payload_size (8 bytes)               |
|   - checksum    (32 bytes, SHA-256)      |
+------------------------------------------+
| Encrypted/Compressed Payload             |
+------------------------------------------+
| AUTH TAG (16 bytes, if encrypted)        |
+------------------------------------------+
| FOOTER: \xff\x00PHTM\xff\x00  (8 bytes) |  (marks end of payload)
+------------------------------------------+
```

### Multi-file Packing

When hiding multiple files, they are packed into a single binary blob before compression/encryption:

```
[file_count: uint32]
For each file:
  [filename_length: uint16]
  [filename: bytes]
  [data_length: uint64]
  [data: bytes]
```

### Extraction Process

Extraction reverses the pipeline:

```
1. Scan file from end → find FOOTER magic
2. Scan file from start → find MAGIC bytes
3. Parse header → read flags, filename, payload size, checksum
4. Extract raw payload bytes
5. Decrypt (if ENCRYPTED flag set) → using password + nonce + salt + auth_tag
6. Decompress (if COMPRESSED flag set) → zlib decompress
7. Verify SHA-256 checksum against header value
8. Write extracted file(s) to output directory
```

### Key Design Decisions

- **Checksum on plaintext**: SHA-256 is computed on the original uncompressed data before any transformation. This ensures integrity verification works regardless of compression/encryption state.
- **Constant-time comparison**: Checksum verification uses `hmac.compare_digest()` to prevent timing side-channel attacks.
- **Filename sanitization**: Extracted filenames are stripped of directory components to prevent path traversal attacks (e.g., `../../etc/passwd` becomes `passwd`).
- **Backward-compatible magic**: The binary MAGIC bytes remain fixed across versions. The header includes a version field for future format evolution.

## Security

- **AES-256-GCM** encryption with authenticated encryption
- **PBKDF2-HMAC-SHA256** key derivation (600,000 iterations)
- **SHA-256** integrity verification with constant-time comparison
- **Path traversal protection** for extracted filenames

## Disclaimer

This tool is for **educational and authorized security research** purposes only. Do not use for illegal activities.

## License

MIT License
