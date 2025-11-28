# Quick Start Guide

Get up and running in 60 seconds.

## One-Time Setup

```bash
# 1. Navigate to the tool directory
cd psforever-password-reset

# 2. Install dependencies (requires Python 3.7+)
pip install -r requirements.txt

# Done! You're ready to use the tool.
```

## Reset a Password (Local Database)

```bash
python reset_password.py
```

Follow the interactive prompts:
1. Enter username to reset
2. Enter new password (6+ chars, hidden input)
3. Confirm password
4. Confirm the reset operation
5. Done!

## Reset a Password (Remote Database)

```bash
python reset_password.py --host 192.168.1.100
```

Same interactive flow as above.

## Common Issues

### "Missing required dependency: No module named 'bcrypt'"
**Fix:** Run `pip install -r requirements.txt`

### "Cannot connect to PostgreSQL at localhost:5432"
**Fix:** Start PostgreSQL: `sudo systemctl start postgresql`

### "Authentication failed for user 'psforever'"
**Fix:** Tool will prompt for correct password - enter it and continue

## Full Documentation

See [README.md](README.md) for complete documentation including:
- All command-line options
- Security notes
- Troubleshooting guide
- Technical details on password hashing

## Files

- `reset_password.py` - The main tool (run this)
- `requirements.txt` - Dependencies list
- `password_reset.log` - Auto-created audit log (keep secure!)
- `README.md` - Full documentation
