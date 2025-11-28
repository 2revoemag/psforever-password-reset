# PSForever Password Reset Tool

A standalone command-line utility for resetting user account passwords in PSForever PlanetSide server emulator databases.

## Overview

This tool is designed for **server administrators** who need to reset user passwords in their PSForever server database. It correctly implements the dual-hash password system required for compatibility with both the PlanetSide launcher and test client.

**Key Features:**
- Interactive, user-friendly command-line interface
- Automatic username lookup with case-insensitive search
- Password validation and confirmation
- Updates both password fields for full compatibility
- Audit logging of all password resets
- Transaction-safe database updates
- Graceful error handling with helpful messages
- Supports remote database connections

## Requirements

- **Python 3.7 or higher**
- **PostgreSQL access** to your PSForever server database
- **Administrator privileges** (this tool requires direct database access)

## Installation

### Option 1: Manual Setup

1. Download or clone this directory to your server:
```bash
git clone <repository-url>
cd psforever-password-reset
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the tool:
```bash
python reset_password.py
```

### Option 2: Standalone Distribution

If you received this as a standalone package:

1. Extract the archive
2. Navigate to the directory
3. Run: `pip install -r requirements.txt`
4. Run: `python reset_password.py`

## Usage

### Basic Usage (Local Database)

If your PostgreSQL database is running on localhost with default credentials:

```bash
python reset_password.py
```

The tool will walk you through an interactive session:

```
============================================================
PSForever Password Reset Tool
============================================================

Connecting to database: psforever@localhost:5432/psforever
✓ Database connection established

Username to reset: TestUser
✓ Found account: TestUser (ID: 42)
  Status: ACTIVE

New password: ********
Confirm password: ********

------------------------------------------------------------
This will reset the password for:
  Account ID: 42
  Username: TestUser (exact case)
  Status: ACTIVE
------------------------------------------------------------
Confirm password reset? [Y/n]: y

Generating password hashes...
Updating database...

✓ Password successfully reset for 'TestUser' (ID: 42)
  Change logged to password_reset.log
```

### Remote Database

If your database is on a remote host:

```bash
python reset_password.py --host 192.168.1.100
```

### Custom Configuration

Override any connection parameter:

```bash
python reset_password.py --host db.example.com --port 5432 --user admin --db psforever_production
```

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | localhost | Database host address |
| `--port` | 5432 | Database port |
| `--user` | psforever | Database username |
| `--db` | psforever | Database name |

## Interactive Prompts

The tool includes intelligent fallback prompts for common scenarios:

### Database Password Prompt
If the default password fails, you'll be prompted:
```
Authentication failed for user 'psforever'
Database password for user 'psforever': ********
```

### Database Name Prompt
If the specified database doesn't exist:
```
Database 'psforever' not found on localhost:5432
Database name (or Ctrl+C to exit):
```

### Account Not Found
If a username isn't found:
```
✗ Account 'InvalidUser' not found.
Try another username? [Y/n]:
```

### Inactive Account Warning
If resetting password for an inactive account:
```
WARNING: Account 'TestUser' is marked INACTIVE
Password will be reset but account remains inactive.
Continue? [y/N]:
```

## Security Notes

**For Server Administrators:**

1. **Database Access Required**: This tool requires direct PostgreSQL access with UPDATE privileges on the `account` table. Only run this on trusted systems.

2. **Audit Logging**: All password resets are logged to `password_reset.log` with timestamps and account details. This file contains usernames - **never share it publicly or commit it to version control**.

3. **Password Storage**: Passwords are **never logged or stored**. Only the bcrypt hashes are written to the database.

4. **Network Security**: When connecting to remote databases, ensure you're using a secure network (VPN, SSH tunnel, or private LAN).

5. **User Permissions**: This tool should only be accessible to server administrators. Regular users should use in-game password reset mechanisms (if available).

## Technical Details

### Dual-Hash Password System

PSForever uses two password fields for compatibility with different PlanetSide clients:

**Field 1: `password` (Launcher Hash)**
- Two-stage process for launcher compatibility
- Stage 1: SHA-256(username + password) using exact case username
- Stage 2: Bcrypt the SHA-256 hash (12 rounds)

**Field 2: `passhash` (Test Client Hash)**
- Direct Bcrypt of plaintext password (12 rounds)
- Used by development test clients

**Both fields must be updated** for users to log in successfully.

### Username Case Sensitivity

- **Database storage**: Case-sensitive (username stored exactly as entered during registration)
- **Login authentication**: Case-insensitive (users can log in with any case variation)
- **Password hashing**: Uses exact case from database (critical for launcher hash)

The tool performs case-insensitive username search but uses the exact case from the database for hash generation.

### Database Schema

**Table**: `account`

Relevant fields:
- `id` (INTEGER, PRIMARY KEY) - Account ID
- `username` (VARCHAR 64, UNIQUE) - Account username
- `password` (VARCHAR 60) - Launcher-compatible hash
- `passhash` (VARCHAR 64) - Test client hash
- `inactive` (BOOLEAN) - Account status

## Troubleshooting

### PostgreSQL Not Running

**Error**: `Cannot connect to PostgreSQL at localhost:5432`

**Solution**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start PostgreSQL if stopped
sudo systemctl start postgresql
```

### Wrong Database Credentials

**Error**: `Authentication failed for user 'psforever'`

**Solution**:
- The tool will prompt you for the correct password
- Verify credentials in your PSForever server config
- Check PostgreSQL user permissions: `psql -U postgres -c "\du"`

### Permission Denied

**Error**: `permission denied for table account`

**Solution**:
```sql
-- Grant UPDATE permission to psforever user
GRANT UPDATE ON account TO psforever;
```

### Database Not Found

**Error**: `Database 'psforever' not found`

**Solution**:
- The tool will prompt for the correct database name
- List databases: `psql -U postgres -c "\l"`
- Verify PSForever database exists and is accessible

### Connection Timeout

**Error**: `could not connect to server: Connection timed out`

**Solution**:
- Check firewall rules: `sudo ufw status`
- Verify PostgreSQL is listening on the correct interface
- Edit `/etc/postgresql/*/main/postgresql.conf`: `listen_addresses = '*'`
- Edit `/etc/postgresql/*/main/pg_hba.conf` to allow remote connections

### Python Dependencies Missing

**Error**: `Missing required dependency: No module named 'bcrypt'`

**Solution**:
```bash
pip install -r requirements.txt
```

If you encounter build errors on Linux, install system dependencies:
```bash
# Debian/Ubuntu
sudo apt-get install python3-dev libpq-dev

# RHEL/CentOS
sudo yum install python3-devel postgresql-devel
```

## Testing Checklist

**Before using this tool in production**, test on a non-production system or VM snapshot:

- [ ] VM snapshot taken before first use
- [ ] Test with known account (verify exact username case preserved)
- [ ] Login with new password using PlanetSide launcher
- [ ] Login with new password using test client (if applicable)
- [ ] Verify `password_reset.log` created and formatted correctly
- [ ] Test with non-existent username (should handle gracefully)
- [ ] Test with inactive account (should warn but allow reset)
- [ ] Test with wrong database password (should prompt)
- [ ] Test password mismatch during confirmation (should retry)
- [ ] Test with password under 6 characters (should reject)

## Files

```
psforever-password-reset/
├── reset_password.py     # Main executable script
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── password_reset.log   # Auto-created audit log (do not commit!)
```

## Support

For issues related to:
- **This tool**: Check Troubleshooting section above
- **PSForever server**: Consult PSForever documentation and community
- **PlanetSide client**: Check client compatibility guides

## License

This tool is provided as-is for PSForever server administrators. Distribute freely to other server hosts.

## Changelog

**Version 1.0** (2025-11-27)
- Initial release
- Interactive password reset with confirmation
- Dual-hash system implementation
- Audit logging
- Remote database support
- Comprehensive error handling
