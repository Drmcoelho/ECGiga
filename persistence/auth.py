"""
Simple authentication utilities for ECGiga.

No external dependencies — uses only ``hashlib``, ``hmac``, ``secrets``,
and ``base64`` from the standard library.  Provides password hashing with
salted SHA-256 and a lightweight JWT-like token mechanism.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

# Default secret — MUST be overridden in production via environment variable
_DEFAULT_SECRET = os.environ.get("ECGIGA_SECRET_KEY", "ecgiga-dev-secret-change-me")

# Token validity: 24 hours
_TOKEN_TTL_SECONDS = 86400


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a password with a random 16-byte salt using SHA-256.

    Returns a string in the format ``salt_hex:hash_hex``.
    """
    salt = secrets.token_bytes(16)
    h = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return f"{salt.hex()}:{h}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a ``salt_hex:hash_hex`` string."""
    try:
        salt_hex, expected_hash = hashed.split(":", 1)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, AttributeError):
        return False
    h = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(h, expected_hash)


# ---------------------------------------------------------------------------
# Token generation / verification (simple JWT-like)
# ---------------------------------------------------------------------------


def _b64url_encode(data: bytes) -> str:
    """Base64-URL encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Base64-URL decode, restoring padding."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def generate_token(user_id: str, secret: str | None = None) -> str:
    """Generate a simple signed token containing the user ID and expiry.

    Format: ``header_b64.payload_b64.signature_b64``  (JWT-like).

    Parameters
    ----------
    user_id : str
        The user identifier to embed in the token.
    secret : str, optional
        HMAC signing secret.  Falls back to ``ECGIGA_SECRET_KEY`` env var.

    Returns
    -------
    str
        The encoded token string.
    """
    secret = secret or _DEFAULT_SECRET

    header = {"alg": "HS256", "typ": "ECGiga"}
    payload = {
        "sub": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + _TOKEN_TTL_SECONDS,
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    signature_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_token(token: str, secret: str | None = None) -> dict:
    """Verify and decode a token.

    Parameters
    ----------
    token : str
        The token string previously issued by ``generate_token``.
    secret : str, optional
        HMAC signing secret.

    Returns
    -------
    dict
        The decoded payload (keys: ``sub``, ``iat``, ``exp``).

    Raises
    ------
    ValueError
        If the token is malformed, the signature is invalid, or the
        token has expired.
    """
    secret = secret or _DEFAULT_SECRET

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token must have 3 parts (header.payload.signature)")

    header_b64, payload_b64, signature_b64 = parts

    # Verify signature
    signing_input = f"{header_b64}.{payload_b64}"
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    actual_sig = _b64url_decode(signature_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")

    # Decode payload
    payload_bytes = _b64url_decode(payload_b64)
    payload = json.loads(payload_bytes)

    # Check expiry
    if payload.get("exp", 0) < time.time():
        raise ValueError("Token has expired")

    return payload
