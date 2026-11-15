import pytest
from fastapi.testclient import TestClient
from backend.api import create_app
from backend.config import Settings
from backend.db import MemoryRepository


@pytest.fixture
def repo():
    return MemoryRepository()


@pytest.fixture
def client(repo):
    with TestClient(create_app(repo, Settings(ai_mode="mock", repository="memory"))) as client:
        yield client


@pytest.fixture
def candidate(client):
    assert client.post("/api/demo/candidate").status_code == 200
    return client
