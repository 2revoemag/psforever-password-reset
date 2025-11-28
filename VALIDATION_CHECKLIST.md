# Validation Checklist

This document provides a quick validation checklist for server administrators before distributing or using this tool.

## Pre-Distribution Validation

- [x] **Python 3.7+ compatibility** - Script uses type hints and f-strings (3.7+)
- [x] **Minimal dependencies** - Only 2 external packages (bcrypt, psycopg2-binary)
- [x] **Executable permissions** - Script has execute bit set
- [x] **Syntax validation** - Python syntax check passes
- [x] **Import guard** - Helpful error if dependencies missing
- [x] **Comprehensive README** - Installation, usage, troubleshooting included
- [x] **Security notes** - Warnings about database access and audit log handling

## Code Quality Validation

- [x] **Type hints** - Function signatures include type annotations
- [x] **Docstrings** - All functions documented
- [x] **Error handling** - Database errors caught and rolled back
- [x] **SQL injection protection** - Parameterized queries used
- [x] **Password security** - getpass.getpass() for hidden input
- [x] **Audit logging** - Append-only log with timestamps
- [x] **No hardcoded secrets** - Only defaults, user can override

## Functional Validation (Requires Database)

To validate functionality, run these tests on a non-production database:

### Test 1: Normal Password Reset
```bash
python reset_password.py
# Enter valid username
# Enter password (6+ chars)
# Confirm password
# Verify "✓ Password successfully reset" message
# Check password_reset.log exists and contains entry
```

### Test 2: Username Not Found
```bash
python reset_password.py
# Enter non-existent username
# Verify "✗ Account 'xxx' not found" message
# Verify retry prompt appears
```

### Test 3: Password Too Short
```bash
python reset_password.py
# Enter valid username
# Enter password <6 chars
# Verify "Password must be at least 6 characters" message
```

### Test 4: Password Mismatch
```bash
python reset_password.py
# Enter valid username
# Enter password
# Enter different confirmation
# Verify "Passwords do not match" with retry count
```

### Test 5: Inactive Account Warning
```bash
# Manually set account.inactive = true in database
python reset_password.py
# Enter inactive account username
# Verify "WARNING: Account 'xxx' is marked INACTIVE" message
# Verify "Continue? [y/N]:" prompt (default No)
```

### Test 6: Remote Database
```bash
python reset_password.py --host remote.db.server
# Verify connection to remote host
# Complete password reset
```

### Test 7: Wrong Database Password
```bash
python reset_password.py --user wronguser
# Verify "Authentication failed" message
# Verify password prompt appears
# Enter correct password
# Verify connection succeeds
```

### Test 8: Database Not Running
```bash
sudo systemctl stop postgresql
python reset_password.py
# Verify helpful error message about PostgreSQL not running
sudo systemctl start postgresql
```

### Test 9: Abort Operations
```bash
# Test Ctrl+C at each prompt
# Verify "Aborted by user." message
# Test 'n' at confirmation prompt
# Verify "Aborted." message
```

### Test 10: Verify Login Works
After password reset:
```bash
# Test login with PlanetSide launcher
# Test login with test client (if applicable)
# Both should succeed with new password
```

## Hash Generation Validation

The critical part of this tool is the dual-hash generation. Verify:

### Launcher Hash (password field)
```python
# Username + password → SHA-256 → Bcrypt(12 rounds)
username = "TestUser"  # Exact case from database!
password = "test123"

import hashlib
import bcrypt

salted = (username + password).encode('utf-8')
sha256_hash = hashlib.sha256(salted).hexdigest()
launcher_hash = bcrypt.hashpw(sha256_hash.encode('utf-8'), bcrypt.gensalt(rounds=12))

# Result should be 60 bytes bcrypt hash starting with "$2b$12$"
```

### Test Client Hash (passhash field)
```python
# Direct bcrypt of password
password = "test123"
testclient_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

# Result should be 60 bytes bcrypt hash starting with "$2b$12$"
```

### Database Update Verification
```sql
-- After password reset, verify both fields updated:
SELECT
    id,
    username,
    LENGTH(password) as password_len,
    LENGTH(passhash) as passhash_len,
    LEFT(password, 7) as password_prefix,
    LEFT(passhash, 7) as passhash_prefix
FROM account
WHERE username = 'TestUser';

-- Expected output:
-- password_len: 60
-- passhash_len: 60
-- password_prefix: $2b$12$
-- passhash_prefix: $2b$12$
```

## Distribution Checklist

Before distributing to other server hosts:

- [ ] All code validation tests pass
- [ ] Functional tests completed on test database
- [ ] README reviewed for accuracy
- [ ] No sensitive information in code or docs
- [ ] requirements.txt versions tested and working
- [ ] Script runs on target Python version (3.7+)
- [ ] Script runs on target OS (Linux/Windows/macOS)

## Post-Distribution Support

Remind users to:
1. Take database backups before first use
2. Test on non-production account first
3. Verify both launcher and test client login work
4. Keep `password_reset.log` secure (contains usernames)
5. Report any issues with specific error messages

## Known Limitations

Document these for users:

1. **No password complexity validation** - Tool accepts any password 6+ chars (intentional - let server enforce policy)
2. **No email notification** - Users won't receive email about password change
3. **Requires direct DB access** - Not suitable for end-user self-service
4. **No password history check** - Doesn't prevent reusing old passwords
5. **No rate limiting** - Admin tool, not exposed to untrusted users

These are acceptable for an admin tool but should be documented.
