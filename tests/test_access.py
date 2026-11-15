def test_sessions_and_backend_roles(client):
    assert client.get("/api/dashboard").status_code==401
    client.login("employer")
    assert client.get("/api/dashboard").status_code==403
    assert client.post("/api/assessments",json={"skill":"python"}).status_code==403
    assert client.get("/api/employer/jobs/greenhouse-unknown/candidates").status_code==403
    client.login("candidate")
    assert client.get("/api/employer/jobs").status_code==403
    assert client.post("/api/jobs",json={"title":"Engineer","company":"Demo","description":"A long job description","required_skills":["python"]}).status_code==403


def test_profile_update_cannot_modify_evidence_or_identity(candidate):
    p=candidate.get("/api/dashboard").json()["profile"]
    update={k:p[k] for k in ["name","current_role","target_role","claimed_skills","marketplace_opt_in"]}
    for extra in [{"assessed_skills":[{"skill":"python","score":100}]},{"role":"employer"},{"id":"seed-candidate"}]:
        assert candidate.patch("/api/profile",json={**update,**extra}).status_code==422
    assert candidate.get("/api/dashboard").json()["skills"]==[]


def test_cross_user_assessment_and_opt_in_projection(candidate,repo):
    foreign=repo.partition("USER#seed-candidate","ASSESSMENT#")[0]
    assert candidate.get(f"/api/assessments/{foreign['id']}").status_code==400
    candidate.login("employer")
    result=candidate.get("/api/employer/jobs/demo-ai-engineer/candidates").json()
    assert {c["id"] for c in result}=={"seed-candidate", "seed-student", "seed-switcher"}
    assert all(c["id"]!="seed-private" for c in result)
    assert all("answers" not in c and "claimed_skills" not in c for c in result)


def test_cross_origin_mutations_are_blocked(candidate):
    assert candidate.post("/api/demo/employer",headers={"origin":"https://untrusted.example"}).status_code==403
