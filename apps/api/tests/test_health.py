import pytest
from fastapi.testclient import TestClient

from genesis_api.main import app


def test_liveness(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "genesis-api",
        "version": "0.14.0",
    }
    assert response.headers["x-request-id"]


def test_invalid_request_id_is_replaced(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health/live",
        headers={"x-request-id": "not-a-uuid"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] != "not-a-uuid"


def test_readiness_degrades_when_a_dependency_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_database_ping() -> None:
        raise OSError("database unavailable")

    async def successful_redis_ping() -> None:
        return None

    monkeypatch.setattr(app.state.database, "ping", fail_database_ping)
    monkeypatch.setattr(app.state.redis, "ping", successful_redis_ping)

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["dependencies"]["database"]["status"] == "degraded"
    assert response.json()["dependencies"]["redis"]["status"] == "ok"
