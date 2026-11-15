from pydantic import ValidationError
import pytest
from backend.models import ChatResponse
from backend.auth import InvalidCredentials


def test_runtime_uses_authenticated_new_user(client,monkeypatch):
    from backend import main
    response=client.post("/api/auth/signup",json={"email":"runtime@example.com","password":"Runtime account password 2026!","name":"Runtime User","current_role":"Engineer"})
    uid=response.json()["profile"]["id"]
    token=client.cookies.get("skillpilot_session")
    monkeypatch.setattr(main,"api",client.app)
    observed=[]
    def fake_chat(service,settings,user_id,role,message):
        observed.append((user_id,role))
        return ChatResponse(message="Hello",mode="mock",delegations=[]),[]
    monkeypatch.setattr(main,"chat",fake_chat)
    result=main.invoke({"message":"Hello","session_token":token})
    assert result["message"]=="Hello"
    assert observed==[(uid,"candidate")]
    assert uid!="candidate-demo"


def test_runtime_rejects_invalid_session_and_identity_override(client,monkeypatch):
    from backend import main
    monkeypatch.setattr(main,"api",client.app)
    with pytest.raises(InvalidCredentials):
        main.invoke({"message":"Hello","session_token":"invalid-session-token-that-is-long-enough"})
    with pytest.raises(ValidationError):
        main.invoke({"message":"Hello","session_token":"invalid-session-token-that-is-long-enough","uid":"candidate-demo"})
