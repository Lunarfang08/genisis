from fastapi.testclient import TestClient

from tests.test_auth_worlds import csrf_headers, register


def create_world(client: TestClient) -> str:
    register(client)
    response = client.post(
        "/api/v1/worlds",
        headers=csrf_headers(client),
        json={
            "name": "Release World",
            "seed": 25,
            "tick_rate": 3,
            "initial_population": 40,
            "city_count": 2,
            "scenario": "rapid_growth",
        },
    )
    assert response.status_code == 201
    assert response.json()["settings"]["scenario"] == "rapid_growth"
    return str(response.json()["id"])


def test_scenarios_capacity_map_analytics_and_exports(client: TestClient) -> None:
    world_id = create_world(client)
    scenarios = client.get("/api/v1/world-scenarios")
    assert scenarios.status_code == 200
    assert len(scenarios.json()) == 7
    capacity = client.get("/api/v1/capacity-projection?citizens=10000").json()
    assert capacity["recommended_tier"] == "worker"

    world_map = client.get(f"/api/v1/worlds/{world_id}/map")
    assert world_map.status_code == 200
    assert len(world_map.json()["cities"]) == 2
    assert sum(city["population"] for city in world_map.json()["cities"]) == 40
    analytics = client.get(f"/api/v1/worlds/{world_id}/analytics")
    assert analytics.status_code == 200
    assert analytics.json()["series"]

    for format_name, content_type in (
        ("json", "application/json"),
        ("csv", "text/csv"),
        ("summary", "text/plain"),
    ):
        export = client.get(f"/api/v1/worlds/{world_id}/export?format={format_name}")
        assert export.status_code == 200
        assert content_type in export.headers["content-type"]


def test_release_security_and_admin_surface(client: TestClient) -> None:
    create_world(client)
    response = client.get("/api/v1/admin/overview")
    assert response.status_code == 200
    assert response.json()["owned_worlds"] == 1
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_world_creation_rejects_unsafe_capacity(client: TestClient) -> None:
    register(client)
    response = client.post(
        "/api/v1/worlds",
        headers=csrf_headers(client),
        json={"name": "Too Sparse", "seed": 1, "initial_population": 10, "city_count": 2},
    )
    assert response.status_code == 422
