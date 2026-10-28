"""Generate a bcrypt password hash for the ADMIN_PASSWORD_HASH env var.

Usage:  python generate_password_hash.py "myAdminPassword"
"""

import sys

import bcrypt


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python generate_password_hash.py <password>")
        sys.exit(1)
    password = sys.argv[1]
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    print(hashed)


if __name__ == "__main__":
    main()
