from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Response

from genesis_api.core.settings import Settings

ACCESS_COOKIE = "genesis_access"
REFRESH_COOKIE = "genesis_refresh"
CSRF_COOKIE = "genesis_csrf"
CSRF_HEADER = "x-csrf-token"

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerifyMismatchError):
        return False


def create_access_token(user_id: UUID, settings: Settings) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_minutes),
        },
        settings.auth_secret_key,
        algorithm="HS256",
    )


def decode_access_token(token: str, settings: Settings) -> UUID | None:
    try:
        payload = jwt.decode(token, settings.auth_secret_key, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        return UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None


def new_refresh_token() -> str:
    return token_urlsafe(48)


def token_digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def set_session_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
    settings: Settings,
) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        httponly=True,
        max_age=settings.access_token_minutes * 60,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        max_age=settings.refresh_token_days * 86_400,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        httponly=False,
        max_age=settings.refresh_token_days * 86_400,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
        path="/",
    )


def clear_session_cookies(response: Response, settings: Settings) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(
            name,
            path="/",
            domain=settings.cookie_domain,
            secure=settings.cookie_secure,
            samesite="lax",
        )
