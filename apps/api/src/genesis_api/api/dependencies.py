from collections.abc import AsyncIterator
from secrets import compare_digest
from typing import Annotated

from fastapi import Cookie, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from genesis_api.api.errors import ApiError
from genesis_api.core.security import (
    ACCESS_COOKIE,
    CSRF_COOKIE,
    CSRF_HEADER,
    decode_access_token,
)
from genesis_api.db.models import User


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async for session in request.app.state.database.session():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def current_user(
    request: Request,
    session: SessionDep,
    access_token: Annotated[str | None, Cookie(alias=ACCESS_COOKIE)] = None,
) -> User:
    user_id = decode_access_token(access_token or "", request.app.state.settings)
    if user_id is None:
        raise ApiError(
            401, "Unauthorized", "Authentication is required.", "authentication_required"
        )
    user = await session.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None:
        raise ApiError(401, "Unauthorized", "The session is no longer valid.", "invalid_session")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


async def require_csrf(
    csrf_cookie: Annotated[str | None, Cookie(alias=CSRF_COOKIE)] = None,
    csrf_header: Annotated[str | None, Header(alias=CSRF_HEADER)] = None,
) -> None:
    if csrf_cookie is None or csrf_header is None or not compare_digest(csrf_cookie, csrf_header):
        raise ApiError(403, "Forbidden", "The CSRF token is missing or invalid.", "csrf_failed")


CsrfProtected = Annotated[None, Depends(require_csrf)]
