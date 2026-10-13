"""Unlock an account and set a new password. Keeps all data.

Run on the server, from the project folder, with the venv active:
    python scripts/reset_password.py admin "NewPassw0rd123"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.core.db import get_conn, init_db  # noqa: E402
from backend.core.security import (  # noqa: E402
    hash_password,
    validate_password_strength,
)


def main() -> int:

    if len(sys.argv) != 3:
        print(__doc__)
        return 1

    username, password = sys.argv[1], sys.argv[2]

    try:
        validate_password_strength(password)
    except ValueError as exc:
        print(f"Password rejected: {exc}")
        return 1

    init_db()

    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE users SET password_hash = ?, failed_attempts = 0, "
            "locked_until = NULL, is_active = 1, "
            "token_version = token_version + 1 WHERE username = ?",
            (hash_password(password), username),
        )

    if cur.rowcount == 0:
        print(f"No user named '{username}'.")
        return 1

    print(f"Done. '{username}' is unlocked with the new password.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
