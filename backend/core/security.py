"""Password hashing and token helpers."""

import base64
import hashlib
import hmac
import os
import re
from datetime import datetime, timedelta, timezone

import jwt

from backend.core import config

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


def hash_password(password: str) -> str:

    salt = os.urandom(16)

    digest = hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
    )

    return "scrypt${}${}".format(
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:

    try:
        scheme, salt_b64, digest_b64 = stored.split("$")

        if scheme != "scrypt":
            return False

        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)

        actual = hashlib.scrypt(
            password.encode(),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
        )

        return hmac.compare_digest(actual, expected)

    except Exception:
        return False


def validate_password_strength(password: str) -> None:

    if len(password) < config.MIN_PASSWORD_LENGTH:
        raise ValueError(
            "Password must be at least "
            f"{config.MIN_PASSWORD_LENGTH} characters."
        )

    if not (
        any(c.isalpha() for c in password)
        and any(c.isdigit() for c in password)
    ):
        raise ValueError(
            "Password must contain letters and numbers."
        )


def validate_username(username: str) -> None:

    if not USERNAME_PATTERN.match(username):
        raise ValueError(
            "Username must be 3-32 characters: "
            "letters, numbers, '.', '_' or '-'."
        )


def create_token(user_id: int, token_version: int) -> str:

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "ver": token_version,
        "iat": now,
        "exp": now + timedelta(
            minutes=config.TOKEN_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        config.SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:

    return jwt.decode(
        token,
        config.SECRET_KEY,
        algorithms=[config.JWT_ALGORITHM],
    )
