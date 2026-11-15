import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.api import create_app
from backend.config import Settings
from backend.db import MemoryRepository


@pytest.fixture
def repo():
    return MemoryRepository()


class AccountClient(TestClient):
    def login(self, actor):
        credentials=json.loads(Path(self.app.state.auth.settings.actor_credentials_path).read_text())[actor]
        return self.post("/api/auth/login",json=credentials)


@pytest.fixture
def client(repo, tmp_path):
    settings=Settings(ai_mode="mock", repository="memory", actor_credentials_path=str(tmp_path/"actors.json"))
    with AccountClient(create_app(repo, settings)) as client:
        yield client


@pytest.fixture
def candidate(client):
    assert client.login("candidate").status_code == 200
    return client
