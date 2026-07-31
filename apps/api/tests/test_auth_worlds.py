from collections.abc import AsyncIterator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from genesis_api.main import app


def csrf_headers(client: TestClient) -> dict[str, str]:
    return {"x-csrf-token": client.cookies["genesis_csrf"]}


def register(client: TestClient, email: str = "observer@example.com") -> dict[str, Any]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": "Primary Observer",
            "password": "correct horse battery staple",
        },
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


def test_register_current_user_logout_and_login(client: TestClient) -> None:
    registered = register(client)
    assert registered["user"]["email"] == "observer@example.com"
    assert client.get("/api/v1/auth/me").status_code == 200

    missing_csrf = client.post("/api/v1/auth/logout")
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["code"] == "csrf_failed"

    logout = client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "OBSERVER@example.com",
            "password": "correct horse battery staple",
        },
    )
    assert login.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200


def test_refresh_rotates_the_refresh_cookie(client: TestClient) -> None:
    register(client)
    old_refresh = client.cookies["genesis_refresh"]
    response = client.post("/api/v1/auth/refresh", headers=csrf_headers(client))
    assert response.status_code == 200
    assert client.cookies["genesis_refresh"] != old_refresh


def test_world_crud_and_owner_authorization(client: TestClient) -> None:
    register(client)
    created = client.post(
        "/api/v1/worlds",
        json={"name": "Aurora", "seed": 42, "tick_rate": 2},
        headers=csrf_headers(client),
    )
    assert created.status_code == 201
    world_id = created.json()["id"]
    assert created.json()["settings"]["seed"] == 42
    assert len(client.get("/api/v1/worlds").json()["items"]) == 1
    assert client.get(f"/api/v1/worlds/{world_id}").status_code == 200

    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    register(client, "second@example.com")
    hidden = client.get(f"/api/v1/worlds/{world_id}")
    assert hidden.status_code == 404
    assert hidden.json()["code"] == "world_not_found"
    assert (
        client.delete(f"/api/v1/worlds/{world_id}", headers=csrf_headers(client)).status_code == 404
    )


def test_validation_uses_consistent_problem_details(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "invalid", "display_name": "x", "password": "short"},
    )
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "validation_failed"


def test_database_failure_is_cors_safe(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failed_session() -> AsyncIterator[AsyncSession]:
        raise SQLAlchemyError("database credentials rejected")
        yield

    monkeypatch.setattr(app.state.database, "session", failed_session)
    response = client.post(
        "/api/v1/auth/register",
        headers={"origin": "http://localhost:3000"},
        json={
            "email": "observer@example.com",
            "display_name": "Primary Observer",
            "password": "correct horse battery staple",
        },
    )

    assert response.status_code == 503
    assert response.json()["code"] == "database_unavailable"
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
