# Security Policy

## Supported Versions

| Version | Supported |
|---------|----------|
| 1.0.x   | ✅        |

## Reporting a Vulnerability

Please report security vulnerabilities by opening a GitHub Issue with the label `security`.

Do NOT include sensitive information (keys, passwords, actual hidden files) in public issues.

## Security Features

- AES-256-GCM authenticated encryption
- PBKDF2-HMAC-SHA256 key derivation (600,000 iterations, OWASP 2023)
- SHA-256 integrity verification with constant-time comparison
- Path traversal protection for extracted filenames
