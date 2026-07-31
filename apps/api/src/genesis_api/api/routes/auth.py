import logging
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID, uuid4

from fastapi import APIRouter, Cookie, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from genesis_api.api.dependencies import CsrfProtected, CurrentUser, SessionDep
from genesis_api.api.errors import ApiError
from genesis_api.api.schemas.auth import (
    LoginRequest,
    RegistrationRequest,
    SessionResponse,
    UserResponse,
)
from genesis_api.core.security import (
    REFRESH_COOKIE,
    clear_session_cookies,
    create_access_token,
    hash_password,
    new_refresh_token,
    set_session_cookies,
    token_digest,
    verify_password,
)
from genesis_api.db.models import RefreshSession, User

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger("genesis_api.auth")


async def _rate_limit(request: Request, action: str) -> None:
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    client = forwarded or (request.client.host if request.client else "unknown")
    allowed = await request.app.state.redis.allow_request(
        f"auth:{action}:{client}", request.app.state.settings.auth_rate_limit, 60
    )
    if not allowed:
        raise ApiError(429, "Too Many Requests", "Try again in one minute.", "rate_limited")


async def _issue_session(
    response: Response,
    session: SessionDep,
    user: User,
    request: Request,
    *,
    family_id: UUID | None = None,
) -> None:
    settings = request.app.state.settings
    refresh_token = new_refresh_token()
    refresh_session = RefreshSession(
        user_id=user.id,
        family_id=family_id or uuid4(),
        token_hash=token_digest(refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
    )
    session.add(refresh_session)
    await session.commit()
    set_session_cookies(
        response,
        access_token=create_access_token(user.id, settings),
        refresh_token=refresh_token,
        csrf_token=token_urlsafe(32),
        settings=settings,
    )


@router.post(
    "/register",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegistrationRequest,
    request: Request,
    response: Response,
    session: SessionDep,
) -> SessionResponse:
    await _rate_limit(request, "register")
    user = User(
        email=str(payload.email).strip().lower(),
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as error:
        await session.rollback()
        logger.info(
            "registration_rejected",
            extra={"auth_event": "registration_rejected", "reason": "email_exists"},
        )
        raise ApiError(
            409, "Account exists", "An account already uses that email.", "email_exists"
        ) from error
    await _issue_session(response, session, user, request)
    logger.info(
        "account_created",
        extra={"auth_event": "account_created", "user_id": str(user.id)},
    )
    return SessionResponse(user=UserResponse.model_validate(user))


@router.post("/login", response_model=SessionResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: SessionDep,
) -> SessionResponse:
    await _rate_limit(request, "login")
    user = await session.scalar(
        select(User).where(User.email == str(payload.email).strip().lower())
    )
    if (
        user is None
        or not user.is_active
        or not verify_password(user.password_hash, payload.password)
    ):
        logger.info(
            "login_rejected",
            extra={"auth_event": "login_rejected", "reason": "invalid_credentials"},
        )
        raise ApiError(401, "Sign in failed", "Email or password is incorrect.", "invalid_login")
    await _issue_session(response, session, user, request)
    logger.info(
        "login_succeeded",
        extra={"auth_event": "login_succeeded", "user_id": str(user.id)},
    )
    return SessionResponse(user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=SessionResponse)
async def refresh(
    request: Request,
    response: Response,
    session: SessionDep,
    _csrf: CsrfProtected,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
) -> SessionResponse:
    settings = request.app.state.settings
    stored = await session.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == token_digest(refresh_token or ""))
    )
    now = datetime.now(UTC)
    if stored is None:
        clear_session_cookies(response, settings)
        raise ApiError(401, "Unauthorized", "The refresh session is invalid.", "invalid_refresh")
    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if stored.revoked_at is not None or expires_at <= now:
        await session.execute(
            update(RefreshSession)
            .where(RefreshSession.family_id == stored.family_id)
            .values(revoked_at=now)
        )
        await session.commit()
        clear_session_cookies(response, settings)
        raise ApiError(401, "Unauthorized", "The refresh session was revoked.", "refresh_reuse")

    stored.revoked_at = now
    user = await session.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise ApiError(401, "Unauthorized", "The account is unavailable.", "invalid_session")
    await _issue_session(response, session, user, request, family_id=stored.family_id)
    return SessionResponse(user=UserResponse.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    session: SessionDep,
    _csrf: CsrfProtected,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
) -> None:
    if refresh_token:
        stored = await session.scalar(
            select(RefreshSession).where(RefreshSession.token_hash == token_digest(refresh_token))
        )
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)
            await session.commit()
    clear_session_cookies(response, request.app.state.settings)
