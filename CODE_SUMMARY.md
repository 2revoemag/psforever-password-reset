# Code Summary

Technical overview of the password reset tool implementation.

## Project Statistics

- **Total Lines**: ~380 lines of Python
- **Dependencies**: 2 packages (bcrypt, psycopg2-binary)
- **Functions**: 8 core functions + main()
- **File Size**: 12KB (reset_password.py)

## Architecture

```
User Input
    ↓
Interactive CLI (argparse + getpass)
    ↓
Database Connection (with fallback prompts)
    ↓
Account Lookup (case-insensitive)
    ↓
Password Validation (min length, confirmation)
    ↓
Hash Generation (dual-hash system)
    ↓
Database Update (transaction-safe)
    ↓
Audit Logging (append-only)
```

## Function Breakdown

### 1. `generate_launcher_hash(username, password) -> bytes`
**Purpose**: Generate launcher-compatible password hash
**Algorithm**:
```python
salted = (username + password).encode('utf-8')
sha256_hash = hashlib.sha256(salted).hexdigest()
launcher_hash = bcrypt.hashpw(sha256_hash.encode('utf-8'), bcrypt.gensalt(rounds=12))
```
**Critical**: Uses exact case username from database

### 2. `generate_testclient_hash(password) -> bytes`
**Purpose**: Generate test client password hash
**Algorithm**:
```python
testclient_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
```
**Note**: Direct bcrypt, no SHA-256 stage

### 3. `connect_database(host, port, user, database, password) -> connection`
**Purpose**: Establish PostgreSQL connection with intelligent fallbacks
**Features**:
- Tries default password first (psforever/psforever)
- Prompts for password if auth fails
- Prompts for database name if not found
- Helpful error messages for common issues
- Max 3 retry attempts
- 10 second connection timeout

**Error Handling**:
- `OperationalError` with 'authentication failed' → Password prompt
- `OperationalError` with 'database does not exist' → Database name prompt
- `OperationalError` with 'connection refused' → PostgreSQL not running error
- Other errors → Generic error with retry

### 4. `find_account(conn, username_search) -> (id, username, inactive) | None`
**Purpose**: Lookup account by username (case-insensitive)
**Query**:
```sql
SELECT id, username, inactive
FROM account
WHERE LOWER(username) = LOWER(%s)
```
**Returns**: Tuple with exact case username or None

### 5. `update_password(conn, account_id, launcher_hash, testclient_hash) -> bool`
**Purpose**: Update both password fields atomically
**Query**:
```sql
UPDATE account
SET password = %s, passhash = %s
WHERE id = %s
```
**Features**:
- Transaction-safe (commit on success, rollback on error)
- Both fields updated together (atomic operation)
- Returns success boolean

### 6. `get_password_input(min_length=6) -> str`
**Purpose**: Get password with validation
**Features**:
- Hidden input via `getpass.getpass()`
- Minimum length enforcement
- Retry loop until valid

### 7. `confirm_password(original, max_attempts=3) -> str | None`
**Purpose**: Confirm password with retry logic
**Features**:
- Hidden input
- Max 3 attempts
- Shows remaining attempts
- Returns None if all attempts fail

### 8. `main()`
**Purpose**: Main execution flow orchestration
**Flow**:
1. Parse command-line arguments
2. Connect to database (with fallbacks)
3. Find account (with retry option)
4. Get new password (with validation)
5. Confirm password (with retry)
6. Show dry-run summary
7. Get user confirmation
8. Generate hashes
9. Update database
10. Log to audit file
11. Show success message

**Exit Codes**:
- `0` - Success or user abort
- `1` - Error (missing dependencies, connection failure, update failure)

## Error Handling Strategy

### Graceful Degradation
- Default credentials fail → Prompt for correct ones
- Database not found → Prompt for database name
- Account not found → Offer retry
- Password mismatch → Allow 3 retries

### Fail-Fast Errors
- PostgreSQL not running → Exit with helpful message
- Max connection attempts → Exit
- Database update fails → Rollback and exit

### User-Friendly Messages
```python
# Bad
"Error: OperationalError(08006)"

# Good
"Cannot connect to PostgreSQL at localhost:5432
Possible causes:
  - PostgreSQL server is not running
  - Server is not accepting connections on this address
Check PostgreSQL status: sudo systemctl status postgresql"
```

## Security Measures

### 1. Hidden Password Input
```python
password = getpass.getpass("New password: ")
```
Never echoed to terminal, not stored in shell history.

### 2. SQL Injection Prevention
```python
# Parameterized queries - safe
cur.execute("UPDATE account SET password = %s WHERE id = %s", (hash, id))

# String concatenation - NEVER used
# cur.execute(f"UPDATE account SET password = '{hash}' WHERE id = {id}")
```

### 3. Audit Logging
```python
audit_log.info(f"Password reset for account ID: {account_id}, username: {exact_username}")
# Passwords and hashes NEVER logged
```

### 4. Transaction Safety
```python
try:
    cur.execute("UPDATE ...")
    conn.commit()  # Only on success
except:
    conn.rollback()  # Undo on any error
```

## Input Validation

### Username
- Not empty (enforced by input loop)
- Case-insensitive lookup
- Must exist in database

### Password
- Minimum 6 characters
- Must match confirmation
- No maximum (bcrypt handles long passwords)
- No complexity requirements (intentional - let server policy decide)

### Database Connection
- Host: Any valid hostname/IP
- Port: Must be integer (argparse enforces)
- User: Any string
- Database: Any string

## Output Formats

### Success Message
```
✓ Password successfully reset for 'TestUser' (ID: 42)
  Change logged to password_reset.log
```

### Error Message
```
✗ Account 'InvalidUser' not found.
Try another username? [Y/n]:
```

### Warning Message
```
WARNING: Account 'TestUser' is marked INACTIVE
Password will be reset but account remains inactive.
Continue? [y/N]:
```

### Audit Log Format
```
2025-11-27 14:32:15 - Password reset for account ID: 42, username: TestUser
```

## Dependencies Deep Dive

### bcrypt (4.1.2)
**Used for**: Password hashing
**Why this version**: Stable, widely tested, CVE-free
**Key functions**:
- `bcrypt.gensalt(rounds=12)` - Generate salt with cost factor 12
- `bcrypt.hashpw(password, salt)` - Hash password with salt

**Cost factor 12**: Balance between security and performance
- Higher = more secure but slower
- PSForever standard = 12 rounds
- ~250ms per hash on modern CPU

### psycopg2-binary (2.9.9)
**Used for**: PostgreSQL database access
**Why binary**: No compilation required, easier installation
**Key functions**:
- `psycopg2.connect()` - Database connection
- `cursor.execute()` - Parameterized queries
- `conn.commit()` / `conn.rollback()` - Transaction control

**Connection pooling**: Not used (single-threaded admin tool)

## Testing Approach

### Manual Testing Required
This tool requires live database for testing:
1. Create test database with sample accounts
2. Run all test scenarios (see VALIDATION_CHECKLIST.md)
3. Verify password hashes match expected format
4. Test actual login with new passwords

### Unit Testing (Future)
Could add:
```python
def test_launcher_hash_generation():
    username = "TestUser"
    password = "test123"
    hash1 = generate_launcher_hash(username, password)
    hash2 = generate_launcher_hash(username, password)

    # Different salts = different hashes
    assert hash1 != hash2

    # Both should verify
    assert bcrypt.checkpw(hash_password(username, password), hash1)
    assert bcrypt.checkpw(hash_password(username, password), hash2)
```

### Integration Testing (Future)
Could add Docker-based testing:
1. Spin up PostgreSQL container
2. Load test schema
3. Run password reset
4. Verify database state
5. Cleanup

## Performance Characteristics

### Time Complexity
- Database lookup: O(1) - indexed username
- Hash generation: O(1) - bcrypt cost factor 12
- Database update: O(1) - single row update

### Actual Timings (approximate)
- Database connection: 10-100ms
- Account lookup: 5-20ms
- Hash generation: 500ms (2 hashes × 250ms)
- Database update: 10-50ms
- Total: ~600ms (dominated by bcrypt)

### Memory Usage
- Script size: <1MB in memory
- No large data structures
- Connection pooling: Not used
- Peak memory: <10MB

### Concurrency
- **Not designed for concurrent use**
- Single-threaded, blocking I/O
- Running multiple instances simultaneously = safe (database handles locking)
- Each instance operates independently

## Edge Cases Handled

1. **Empty username** → Reject and re-prompt
2. **Username with special chars** → Passed as-is (database validates)
3. **Very long password** → Bcrypt handles (max 72 bytes, longer truncated)
4. **Unicode in password** → UTF-8 encoded before hashing
5. **Inactive account** → Warn but allow reset
6. **Account ID doesn't exist** → Database constraint prevents
7. **Ctrl+C at any prompt** → Graceful exit with "Aborted by user"
8. **Connection timeout** → 10 second timeout, clear error message
9. **Duplicate username** (impossible due to UNIQUE constraint)
10. **NULL values in database** → psycopg2 handles appropriately

## Known Limitations

1. **No concurrent access protection** - Multiple admins resetting same account = race condition
2. **No password history** - Can reuse old passwords
3. **No email notification** - User doesn't know password changed
4. **No rate limiting** - Admin tool, trusted users
5. **No audit of failed attempts** - Only successful resets logged
6. **No password complexity validation** - Accepts any 6+ char password
7. **No 2FA reset** - Only password reset
8. **No session invalidation** - Active sessions remain valid

These are acceptable for an admin tool but should be documented.

## Future Enhancement Ideas

### v1.1.0 Candidates
- Email notification on password change
- Password strength meter
- Batch reset from CSV file
- Export audit log to CSV
- Colorized output (termcolor)

### v1.2.0 Candidates
- Password complexity rules (configurable)
- Force logout of active sessions
- Last login timestamp display
- Account statistics (created, last login, reset count)

### v2.0.0 Candidates
- Web interface (Flask/FastAPI)
- API endpoint version
- Multi-server support (manage multiple databases)
- LDAP/Active Directory integration
- Two-factor authentication reset

### Code Quality Improvements
- Add type checking (mypy)
- Add unit tests (pytest)
- Add integration tests (docker-compose)
- Add linting (pylint/flake8)
- Add code coverage (coverage.py)

## Maintenance Notes

### Updating Dependencies
```bash
# Check for updates
pip list --outdated

# Update requirements.txt
pip freeze > requirements.txt

# Test thoroughly before distributing
```

### Testing After Dependency Update
1. Verify bcrypt hashes still verify with old hashes
2. Verify database connection still works
3. Run full validation checklist
4. Test on Python 3.7, 3.8, 3.9, 3.10, 3.11

### Security Updates
Monitor CVEs for:
- bcrypt (password hashing library)
- psycopg2 (PostgreSQL driver)
- Python itself

Sign up for:
- GitHub security advisories
- PyPI security notifications
- PSForever security mailing list

## Deployment Recommendations

### For Server Admins

**Install location**: `/opt/psforever/tools/password-reset/`

**Permissions**:
```bash
chmod 755 reset_password.py  # Executable
chmod 644 requirements.txt README.md  # Read-only
chmod 600 password_reset.log  # Admin read/write only (created by tool)
```

**Access control**:
- Only root and trusted admins
- sudo required for execution
- Audit who has access

**Backup strategy**:
- Database backup before first use
- Test account verification
- Keep old version until new version validated

**Monitoring**:
- Review password_reset.log weekly
- Alert on excessive reset activity
- Correlate with user support tickets
