# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

import base64
import hashlib
import hmac
import secrets

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16


def _b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64_decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        f"pbkdf2_{PBKDF2_ALGORITHM}"
        f"${PBKDF2_ITERATIONS}"
        f"${_b64_encode(salt)}"
        f"${_b64_encode(derived)}"
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded_hash.split("$", maxsplit=3)
        if algorithm != f"pbkdf2_{PBKDF2_ALGORITHM}":
            return False
        salt = _b64_decode(salt_b64)
        expected_digest = _b64_decode(digest_b64)
        calculated_digest = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(expected_digest, calculated_digest)
    except (ValueError, TypeError):
        return False


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)
