# Distribution Package Instructions

This document is for the PSForever project maintainer who wants to distribute this tool to other server hosts.

## What to Distribute

Include these files in the distribution package:

**Required:**
- `reset_password.py` - The main executable
- `requirements.txt` - Python dependencies
- `README.md` - Primary documentation
- `QUICKSTART.md` - Quick start guide

**Optional (but recommended):**
- `VALIDATION_CHECKLIST.md` - For server admins who want to validate before use

**DO NOT include:**
- `password_reset.log` - Auto-created, contains usernames
- `__pycache__/` - Python bytecode cache
- `.git/` - Version control metadata

## Creating Distribution Archive

### Option 1: ZIP Archive (Cross-platform)

```bash
cd /path/to/psforever-password-reset/..
zip -r psforever-password-reset-v1.0.zip psforever-password-reset \
    -x "*.pyc" \
    -x "*__pycache__*" \
    -x "*.log" \
    -x "*.git*"
```

### Option 2: TAR.GZ Archive (Linux/macOS)

```bash
cd /path/to/psforever-password-reset/..
tar -czf psforever-password-reset-v1.0.tar.gz \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    --exclude="*.log" \
    --exclude=".git" \
    psforever-password-reset/
```

## Distribution Checklist

Before distributing:

- [ ] Remove `password_reset.log` if it exists
- [ ] Remove `__pycache__/` directory
- [ ] Verify all required files present
- [ ] Test on fresh Python environment
- [ ] Review README for accuracy
- [ ] Update version number in README changelog
- [ ] Create release notes (see below)

## Release Notes Template

```markdown
# PSForever Password Reset Tool v1.0

## What's New
- Initial release
- Interactive password reset workflow
- Dual-hash system (launcher + test client)
- Audit logging
- Remote database support
- Comprehensive error handling

## Installation
1. Extract archive
2. Run: pip install -r requirements.txt
3. Run: python reset_password.py

## Documentation
See README.md for complete documentation.

## Requirements
- Python 3.7+
- PostgreSQL access to PSForever database
- Server administrator privileges

## Support
For issues, consult README.md troubleshooting section.
```

## Hosting Options

### Option 1: GitHub Release
1. Create release in PSForever repository
2. Upload archive as release asset
3. Link to README.md in release notes

### Option 2: Direct Download
1. Host archive on PSForever website
2. Provide download link in server documentation
3. Include SHA256 checksum for verification

### Option 3: Git Submodule
1. Create separate repository: `psforever-password-reset`
2. Other server hosts can clone or download
3. Easy to update and version independently

## Checksum Generation

Always provide checksums for distributed archives:

```bash
# SHA256 checksum
sha256sum psforever-password-reset-v1.0.tar.gz > psforever-password-reset-v1.0.tar.gz.sha256

# MD5 checksum (for compatibility)
md5sum psforever-password-reset-v1.0.tar.gz > psforever-password-reset-v1.0.tar.gz.md5
```

Users can verify:
```bash
sha256sum -c psforever-password-reset-v1.0.tar.gz.sha256
```

## Version Numbering

Follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR** - Breaking changes (incompatible database schema)
- **MINOR** - New features (backwards compatible)
- **PATCH** - Bug fixes (no feature changes)

Examples:
- `v1.0.0` - Initial release
- `v1.1.0` - Add email notification feature
- `v1.1.1` - Fix typo in error message
- `v2.0.0` - Support new database schema

## Support Expectations

When distributing, set clear expectations:

**What you will support:**
- Bug fixes for current version
- Documentation updates
- Security patches

**What users should handle:**
- Local installation issues
- Database configuration
- Server-specific problems
- Python environment setup

**Response time:**
- Critical security issues: 24-48 hours
- Bug reports: Best effort (community project)
- Feature requests: Consider for future versions

## License Considerations

If adding license file:

```bash
# Add LICENSE file (example: MIT)
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 PSForever Project

Permission is hereby granted, free of charge, to any person obtaining a copy...
EOF
```

Include license in distribution archive.

## Community Distribution

Encourage community contributions:

1. **Issue Tracker** - For bug reports and feature requests
2. **Pull Requests** - For improvements and fixes
3. **Wiki/Docs** - For server-specific setup guides
4. **Forum Thread** - For community support

## Security Disclosure

If distributing widely, provide security contact:

```markdown
## Security Issues

If you discover a security vulnerability in this tool:

1. **DO NOT** open a public issue
2. Email: security@psforever.net (example)
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
4. Allow 30 days for patch before public disclosure
```

## Update Notification

How to notify users of updates:

1. **GitHub Releases** - Users can watch repository
2. **PSForever Forum** - Post announcement
3. **Discord/IRC** - Notify server admin channels
4. **Server Admin Mailing List** - If one exists

## Future Versions

Planning for updates:

**v1.1.0 candidates:**
- Email notification on password change
- Batch password reset from CSV
- Password strength meter
- Two-factor authentication reset

**v2.0.0 candidates:**
- Support for new database schema (if PSForever changes)
- Multi-database support (MySQL, MariaDB)
- Web interface version

Keep versioning backwards compatible where possible.
