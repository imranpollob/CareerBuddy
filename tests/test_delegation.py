import pytest
from backend.config import Settings
from backend.orchestrator import chat


@pytest.mark.parametrize("message,specialists", [
    ("Hello", []),
    ("What skills are in demand?", ["job_market"]),
    ("Prepare a Python assessment", ["assessment"]),
    ("Build my learning roadmap", ["coach"]),
    ("Find jobs that match my skills", ["marketplace"]),
])
def test_actual_nested_agents_select_only_needed_tools(candidate,message,specialists):
    response=candidate.post("/api/chat",json={"message":message})
    assert response.status_code==200
    data=response.json()
    assert [d["specialist"] for d in data["delegations"]]==specialists
    for delegation in data["delegations"]:
        assert delegation["tools"] and delegation["result"]["data"]


def test_chat_history_uses_current_request(candidate):
    candidate.post("/api/chat",json={"message":"Prepare a Python assessment"})
    result=candidate.post("/api/chat",json={"message":"Find jobs that match my skills"}).json()
    assert result["delegations"][0]["specialist"]=="marketplace"


def test_model_failure_returns_retryable_error(candidate,monkeypatch):
    def failed(*args,**kwargs):
        raise RuntimeError("model unavailable")
    monkeypatch.setattr("backend.api.chat",failed)
    response=candidate.post("/api/chat",json={"message":"Hello"})
    assert response.status_code==503
    assert "Your evidence is safe" in response.json()["detail"]
