# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-20

### Added
- Initial release
- AES-256-GCM encryption with PBKDF2-HMAC-SHA256 key derivation
- Multi-file steganography support (hide multiple files in a single carrier)
- zlib compression with adaptive sampling (only applied when size reduction >= 10%)
- Path traversal protection for extracted filenames
- SHA-256 integrity verification with constant-time comparison (`hmac.compare_digest`)
- Binary stacking (polyglot) technique — carrier file remains fully functional
- Cross-platform CLI: Windows, Linux, macOS
- Docker support with `python:3.12-slim` base image
- Rich terminal output with banner display
- Support for any carrier format: PDF, PNG, JPEG, ZIP, MP3, MP4, DOCX, and more
