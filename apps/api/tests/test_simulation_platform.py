from typing import Any, cast
from uuid import UUID

from fastapi.testclient import TestClient

from genesis_api.core.settings import Settings
from genesis_api.main import app
from genesis_api.services.narratives import NarrativeService
from genesis_api.services.simulation_runtime import PersistentSimulationRuntime
from tests.test_auth_worlds import csrf_headers, register


def create_world(client: TestClient) -> str:
    register(client)
    response = client.post(
        "/api/v1/worlds",
        json={
            "name": "Continuum",
            "seed": 73,
            "tick_rate": 2,
            "initial_population": 20,
            "city_count": 1,
        },
        headers=csrf_headers(client),
    )
    assert response.status_code == 201
    return cast(str, response.json()["id"])


def test_new_world_has_a_complete_seeded_civilization(client: TestClient) -> None:
    world_id = create_world(client)

    timeline = client.get(f"/api/v1/worlds/{world_id}/timeline")
    assert timeline.status_code == 200
    assert timeline.json()["items"][0]["event_type"] == "world.civilization_initialized"
    assert client.get(f"/api/v1/worlds/{world_id}/snapshots").json()
    replay = client.get(f"/api/v1/worlds/{world_id}/replay-status").json()
    assert replay["latest_event_sequence"] == 1
    assert replay["replay_event_count"] == 1

    dashboard = client.get(f"/api/v1/worlds/{world_id}/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["population"] == 20
    assert dashboard.json()["latest_metrics"]["population"] == 20
    activity = client.get(f"/api/v1/worlds/{world_id}/ai/activity")
    assert activity.json()["calls"] == 0


def test_controls_are_csrf_protected_validated_and_ordered(client: TestClient) -> None:
    world_id = create_world(client)
    endpoint = f"/api/v1/worlds/{world_id}/controls"

    assert client.post(endpoint, json={"command": "pause"}).status_code == 403
    invalid = client.post(
        endpoint,
        json={"command": "set_speed"},
        headers=csrf_headers(client),
    )
    assert invalid.status_code == 422

    pause = client.post(endpoint, json={"command": "pause"}, headers=csrf_headers(client))
    speed = client.post(
        endpoint,
        json={"command": "set_speed", "speed": 12},
        headers=csrf_headers(client),
    )
    assert pause.status_code == 202
    assert speed.status_code == 202
    pause_body = cast(dict[str, Any], pause.json())
    speed_body = cast(dict[str, Any], speed.json())
    assert pause_body["sequence"] == 1
    assert pause_body["is_paused"] is True
    assert speed_body["sequence"] == 2
    assert speed_body["speed"] == 12


def test_simulation_surfaces_enforce_world_ownership(client: TestClient) -> None:
    world_id = create_world(client)
    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    register(client, "other-observer@example.com")

    for suffix in ("timeline", "dashboard", "snapshots", "replay-status", "ai/activity"):
        response = client.get(f"/api/v1/worlds/{world_id}/{suffix}")
        assert response.status_code == 404


def test_runtime_step_reset_and_mock_narrative_are_persisted(client: TestClient) -> None:
    register(client)
    created = client.post(
        "/api/v1/worlds",
        json={
            "name": "Living World",
            "seed": 91,
            "tick_rate": 2,
            "initial_population": 20,
            "city_count": 1,
            "ai_enabled": True,
            "ai_provider": "mock",
        },
        headers=csrf_headers(client),
    )
    world_id = UUID(created.json()["id"])

    async def advance_and_narrate() -> None:
        async for session in app.state.database.session():
            result = await PersistentSimulationRuntime().tick(session, world_id, single_step=True)
            assert result.advanced is True
            await session.commit()
        async for session in app.state.database.session():
            service = NarrativeService(Settings(ai_enabled=True, ai_provider="mock"))
            assert await service.annotate_next(session) is True

    assert client.portal is not None
    client.portal.call(advance_and_narrate)
    advanced = client.get(f"/api/v1/worlds/{world_id}").json()
    assert advanced["settings"]["simulation_tick"] == 1
    assert advanced["settings"]["simulation_date"] == "2200-01-02"
    assert client.get(f"/api/v1/worlds/{world_id}/ai/activity").json()["calls"] == 1

    async def reset() -> None:
        async for session in app.state.database.session():
            await PersistentSimulationRuntime().reset(session, world_id)
            await session.commit()

    client.portal.call(reset)
    restored = client.get(f"/api/v1/worlds/{world_id}").json()
    assert restored["settings"]["simulation_tick"] == 0
    assert restored["settings"]["simulation_date"] == "2200-01-01"
    assert restored["settings"]["is_paused"] is True
