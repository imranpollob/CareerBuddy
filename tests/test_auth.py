from concurrent.futures import ThreadPoolExecutor
import time
from backend.api import create_app
from backend.auth import account_key, digest
from backend.config import Settings
from backend.db import item
from fastapi.testclient import TestClient


def registration(email="new-user@example.com", role="candidate"):
    return {"email":email,"password":"Test account password 2026!","name":"New User","role":role,
            "current_role":"Student" if role=="candidate" else "Hiring manager","target_role":"AI Engineer",
            "candidate_track":"student","claimed_skills":["python"]}


def test_signup_login_logout_and_persisted_session(client,repo):
    response=client.post("/api/auth/signup",json=registration())
    assert response.status_code==200
    data=response.json()
    assert data["profile"]["synthetic"] is False
    assert data["profile"]["id"] not in {"candidate-demo","student-demo"}
    token=client.cookies.get("skillpilot_session")
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=strict" in response.headers["set-cookie"].lower()
    assert repo.get(f"SESSION#{digest(token)}","AUTH_SESSION")["uid"]==data["profile"]["id"]
    account=repo.get(*account_key("NEW-USER@example.com"))
    assert account["password_hash"].startswith("$argon2id$")
    assert "Test account password" not in account["password_hash"]
    assert "password" not in response.text
    second=create_app(repo,Settings(ai_mode="mock",repository="memory",seed_accounts=False))
    with TestClient(second) as restored:
        restored.cookies.set("skillpilot_session",token)
        assert restored.get("/api/session").json()["email"]=="new-user@example.com"
    assert client.post("/api/auth/logout").status_code==200
    client.cookies.set("skillpilot_session",token,domain="testserver.local")
    assert client.get("/api/session").status_code==401
    assert client.post("/api/auth/login",json={"email":"NEW-USER@example.com","password":registration()["password"]}).status_code==200
    assert client.cookies.get("skillpilot_session")!=token


def test_signup_validation_duplicates_and_no_demo_bypass(client):
    assert client.post("/api/auth/signup",json={**registration(),"password":"1234567"}).status_code==422
    assert client.post("/api/auth/signup",json={**registration(),"email":"invalid"}).status_code==422
    assert client.post("/api/auth/signup",json={**registration(),"uid":"candidate-demo"}).status_code==422
    assert client.post("/api/auth/signup",json={**registration(),"password":"12345678"}).status_code==200
    assert client.post("/api/auth/signup",json=registration("NEW-USER@example.com")).status_code==409
    for actor in ["candidate","student","employer"]:
        assert client.post(f"/api/demo/{actor}").status_code==404


def test_invalid_login_is_generic_and_throttled(client):
    missing=client.post("/api/auth/login",json={"email":"missing@example.com","password":"incorrect"})
    existing=client.post("/api/auth/login",json={"email":"alex@example.com","password":"incorrect"})
    assert missing.status_code==existing.status_code==401
    assert missing.json()==existing.json()
    for _ in range(7):
        client.post("/api/auth/login",json={"email":"missing@example.com","password":"incorrect"})
    assert client.post("/api/auth/login",json={"email":"missing@example.com","password":"incorrect"}).status_code==429


def test_user_isolation_and_employer_ownership(client):
    first=client.post("/api/auth/signup",json=registration()).json()
    attempt=client.post("/api/assessments",json={"skill":"python"}).json()
    client.post("/api/auth/signup",json=registration("other@example.com"))
    assert client.get(f"/api/assessments/{attempt['id']}").status_code==400
    assert client.get("/api/dashboard").json()["skills"]==[]
    assert client.get("/api/employer/jobs").status_code==403
    employer=client.post("/api/auth/signup",json=registration("employer@example.com","employer"))
    assert employer.status_code==200
    assert client.get("/api/employer/jobs").json()==[]
    assert client.get("/api/employer/jobs/demo-junior-ai/candidates").status_code==403
    job=client.post("/api/jobs",json={"title":"AI Engineer","company":"New Team","description":"Build AI applications with Python.","required_skills":["python"]})
    assert job.status_code==200 and job.json()["synthetic"] is False
    assert job.json()["employer_id"]==employer.json()["profile"]["id"]


def test_expired_session_rejected(candidate,repo):
    token=candidate.cookies.get("skillpilot_session")
    repo.write([item(f"SESSION#{digest(token)}","AUTH_SESSION",{"uid":"candidate-demo","email":"alex@example.com","expires_at":int(time.time())-1})])
    assert candidate.get("/api/dashboard").status_code==401


def test_signup_atomic_duplicate_race(client,repo):
    from backend.models import SignupRequest
    from backend.db import Conflict
    auth=client.app.state.auth
    def signup():
        try:
            auth.signup(SignupRequest(**registration()))
            return "created"
        except Conflict:
            return "conflict"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _:signup(),range(2)))==["conflict","created"]
    assert sum(p["name"]=="New User" for p in repo.scan("PROFILE"))==1
