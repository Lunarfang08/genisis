import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ["GENESIS_ENVIRONMENT"] = "test"
os.environ["GENESIS_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["GENESIS_REDIS_URL"] = "redis://127.0.0.1:1/0"

from genesis_api.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
