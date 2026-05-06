# Security Policy

## Reporting a Vulnerability

This is a private M&A research pipeline. If you discover a security issue:

1. **Do not** open a public issue
2. Email the repository owner directly
3. Include a description of the vulnerability and steps to reproduce

## What to Report

- Hardcoded API keys or tokens in source code
- Command injection vulnerabilities
- Exposure of sensitive company data
- Authentication bypasses in integrated APIs

## Secrets Management

- All API keys should be stored in `.env` (gitignored)
- The `Config` class in `core/config.py` is the single source of truth for all secrets
- No hardcoded tokens should exist in `.py` files
- The hardcoded GitHub token `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` has been removed — revoke it at github.com/settings/tokens if you have access
