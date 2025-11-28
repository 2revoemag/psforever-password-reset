#!/usr/bin/env python3
"""
PSForever Password Reset Tool
A standalone utility for resetting user account passwords in PSForever server databases.

This tool updates both password fields required for launcher and test client compatibility.
"""

import sys
import getpass
import hashlib
import argparse
import logging
from datetime import datetime
from typing import Optional, Tuple

try:
    import bcrypt
    import psycopg2
    from psycopg2 import sql
except ImportError as e:
    print(f"ERROR: Missing required dependency: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)


# Configure audit logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('password_reset.log', mode='a'),
    ]
)
audit_log = logging.getLogger('audit')


def generate_launcher_hash(username: str, password: str) -> bytes:
    """
    Generate launcher-compatible password hash (two-stage process).

    Stage 1: SHA-256(username + password) - exact case username required
    Stage 2: Bcrypt the SHA-256 hash (12 rounds)

    Args:
        username: Exact case username from database
        password: Plaintext password

    Returns:
        Bcrypt hash as bytes
    """
    # Stage 1: SHA-256 of concatenated username + password
    salted = (username + password).encode('utf-8')
    sha256_hash = hashlib.sha256(salted).hexdigest()

    # Stage 2: Bcrypt the SHA-256 hash (force version 2a for Scala compatibility)
    launcher_hash = bcrypt.hashpw(sha256_hash.encode('utf-8'), bcrypt.gensalt(rounds=12, prefix=b"2a"))

    return launcher_hash


def generate_testclient_hash(password: str) -> bytes:
    """
    Generate test client password hash (direct bcrypt).

    Args:
        password: Plaintext password

    Returns:
        Bcrypt hash as bytes
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12, prefix=b"2a"))


def connect_database(host: str, port: int, user: str, database: str, password: Optional[str] = None) -> psycopg2.extensions.connection:
    """
    Connect to PostgreSQL database with fallback prompts.

    Args:
        host: Database host
        port: Database port
        user: Database user
        database: Database name
        password: Database password (None = try default first)

    Returns:
        Database connection object

    Raises:
        psycopg2.Error: If connection fails after retries
    """
    max_attempts = 3
    attempt = 0

    # Try default password first
    if password is None:
        password = user  # Default: psforever/psforever

    while attempt < max_attempts:
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connect_timeout=10
            )
            return conn

        except psycopg2.OperationalError as e:
            error_msg = str(e).lower()

            # Database doesn't exist
            if 'database' in error_msg and 'does not exist' in error_msg:
                print(f"\nDatabase '{database}' not found on {host}:{port}")
                database = input("Database name (or Ctrl+C to exit): ").strip()
                if not database:
                    database = 'psforever'
                attempt += 1
                continue

            # Authentication failed
            elif 'authentication failed' in error_msg or 'password' in error_msg:
                print(f"\nAuthentication failed for user '{user}'")
                password = getpass.getpass(f"Database password for user '{user}': ")
                attempt += 1
                continue

            # Connection refused / server not running
            elif 'connection refused' in error_msg or 'could not connect' in error_msg:
                print(f"\nERROR: Cannot connect to PostgreSQL at {host}:{port}")
                print("Possible causes:")
                print("  - PostgreSQL server is not running")
                print("  - Server is not accepting connections on this address")
                print("  - Firewall blocking connection")
                print(f"\nCheck PostgreSQL status: sudo systemctl status postgresql")
                sys.exit(1)

            # Unknown error
            else:
                print(f"\nDatabase connection error: {e}")
                attempt += 1
                if attempt < max_attempts:
                    print(f"Retrying... (attempt {attempt + 1}/{max_attempts})")
                continue

        except Exception as e:
            print(f"\nUnexpected error connecting to database: {e}")
            sys.exit(1)

    print(f"\nFailed to connect after {max_attempts} attempts.")
    sys.exit(1)


def find_account(conn: psycopg2.extensions.connection, username_search: str) -> Optional[Tuple[int, str, bool]]:
    """
    Find account by username (case-insensitive search).

    Args:
        conn: Database connection
        username_search: Username to search for

    Returns:
        Tuple of (account_id, exact_username, is_inactive) or None if not found
    """
    with conn.cursor() as cur:
        # Case-insensitive search
        cur.execute(
            "SELECT id, username, inactive FROM account WHERE LOWER(username) = LOWER(%s)",
            (username_search,)
        )
        result = cur.fetchone()

        if result:
            return (result[0], result[1], result[2])
        return None


def update_password(conn: psycopg2.extensions.connection, account_id: int, launcher_hash: bytes, testclient_hash: bytes) -> bool:
    """
    Update both password fields in the database (transaction-safe).

    Args:
        conn: Database connection
        account_id: Account ID to update
        launcher_hash: Launcher-compatible hash
        testclient_hash: Test client hash

    Returns:
        True if update succeeded, False otherwise
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE account SET password = %s, passhash = %s WHERE id = %s",
                (launcher_hash.decode('utf-8'), testclient_hash.decode('utf-8'), account_id)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"\nERROR: Database update failed: {e}")
        conn.rollback()
        return False


def get_password_input(min_length: int = 6) -> str:
    """
    Get password input with validation.

    Args:
        min_length: Minimum password length

    Returns:
        Validated password
    """
    while True:
        password = getpass.getpass("New password: ")
        if len(password) < min_length:
            print(f"Password must be at least {min_length} characters. Please try again.")
            continue
        return password


def confirm_password(original: str, max_attempts: int = 3) -> Optional[str]:
    """
    Confirm password with retry logic.

    Args:
        original: Original password to match
        max_attempts: Maximum retry attempts

    Returns:
        Password if confirmed, None if max attempts exceeded
    """
    for attempt in range(max_attempts):
        confirm = getpass.getpass("Confirm password: ")
        if confirm == original:
            return confirm

        remaining = max_attempts - attempt - 1
        if remaining > 0:
            print(f"Passwords do not match. {remaining} attempt(s) remaining.")
        else:
            print("Passwords do not match.")

    return None


def main():
    """Main execution flow."""
    parser = argparse.ArgumentParser(
        description='PSForever Password Reset Tool - Reset user account passwords',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reset_password.py
  python reset_password.py --host 192.168.1.100
  python reset_password.py --host localhost --port 5432 --user psforever --db psforever
        """
    )
    parser.add_argument('--host', default='localhost', help='Database host (default: localhost)')
    parser.add_argument('--port', type=int, default=5432, help='Database port (default: 5432)')
    parser.add_argument('--user', default='psforever', help='Database user (default: psforever)')
    parser.add_argument('--db', default='psforever', help='Database name (default: psforever)')

    args = parser.parse_args()

    print("=" * 60)
    print("PSForever Password Reset Tool")
    print("=" * 60)
    print()

    # Connect to database
    print(f"Connecting to database: {args.user}@{args.host}:{args.port}/{args.db}")
    try:
        conn = connect_database(args.host, args.port, args.user, args.db)
        print("✓ Database connection established")
        print()
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    try:
        # Step 1: Find account
        while True:
            username_search = input("Username to reset: ").strip()
            if not username_search:
                print("Username cannot be empty.")
                continue

            account = find_account(conn, username_search)

            if account is None:
                print(f"✗ Account '{username_search}' not found.")
                retry = input("Try another username? [Y/n]: ").strip().lower()
                if retry and retry[0] == 'n':
                    print("Aborted.")
                    sys.exit(0)
                continue

            account_id, exact_username, is_inactive = account
            print(f"✓ Found account: {exact_username} (ID: {account_id})")
            if is_inactive:
                print("  Status: INACTIVE")
            else:
                print("  Status: ACTIVE")
            print()
            break

        # Step 2: Get new password
        while True:
            password = get_password_input(min_length=6)

            # Step 3: Confirm password
            confirmed = confirm_password(password, max_attempts=3)

            if confirmed is None:
                print("\nPassword confirmation failed. Starting over...")
                print()
                continue

            break

        # Step 4: Dry-run confirmation
        print()
        print("-" * 60)
        print("This will reset the password for:")
        print(f"  Account ID: {account_id}")
        print(f"  Username: {exact_username} (exact case)")
        print(f"  Status: {'INACTIVE' if is_inactive else 'ACTIVE'}")
        print("-" * 60)

        if is_inactive:
            print()
            print(f"WARNING: Account '{exact_username}' is marked INACTIVE")
            print("Password will be reset but account remains inactive.")
            confirm = input("Continue? [y/N]: ").strip().lower()
            if not confirm or confirm[0] != 'y':
                print("Aborted.")
                sys.exit(0)
        else:
            confirm = input("Confirm password reset? [Y/n]: ").strip().lower()
            if confirm and confirm[0] == 'n':
                print("Aborted.")
                sys.exit(0)

        # Step 5: Generate hashes
        print()
        print("Generating password hashes...")
        launcher_hash = generate_launcher_hash(exact_username, password)
        testclient_hash = generate_testclient_hash(password)

        # Step 6: Update database
        print("Updating database...")
        if update_password(conn, account_id, launcher_hash, testclient_hash):
            print()
            print("✓ Password successfully reset for '{}' (ID: {})".format(exact_username, account_id))
            print("  Change logged to password_reset.log")

            # Audit log
            audit_log.info(f"Password reset for account ID: {account_id}, username: {exact_username}")
        else:
            print("\n✗ Password reset failed. Database was not modified.")
            sys.exit(1)

    finally:
        conn.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
