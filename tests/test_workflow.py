def test_assessment_learning_matching_and_consent(candidate):
    chat=candidate.post("/api/chat",json={"message":"Prepare a Python assessment"})
    assert chat.status_code==200
    aid=chat.json()["delegations"][0]["result"]["data"]["id"]
    candidate.post(f"/api/assessments/{aid}/submit",json={"answers":{"q1":1,"q2":1,"q3":0,"q4":0}})
    assert candidate.get("/api/dashboard").json()["skills"][0]["passed"] is False
    before=candidate.get("/api/matches").json()
    assert next(m for m in before if m["job"]["id"]=="demo-python-engineer")["supported_count"]==0
    roadmap=candidate.post("/api/chat",json={"message":"Build my learning roadmap"}).json()
    assert roadmap["delegations"][0]["specialist"]=="coach"
    assert candidate.get("/api/lessons/python").json()["exercise"]
    new=candidate.post("/api/lessons/python/complete").json()
    assert new["id"]!=aid
    assert candidate.get("/api/dashboard").json()["skills"][0]["passed"] is False
    result=candidate.post(f"/api/assessments/{new['id']}/submit",json={"answers":{"q1":0,"q2":2,"q3":1,"q4":3}})
    assert result.json()["result"]["passed"] is True
    after=candidate.get("/api/matches").json()
    assert next(m for m in after if m["job"]["id"]=="demo-python-engineer")["supported_count"]==1
    dashboard=candidate.get("/api/dashboard").json()
    assert next(m for m in dashboard["roadmap"]["milestones"] if m["skill"]=="python")["status"]=="completed"
    profile=dashboard["profile"]
    update={k:profile[k] for k in ["name","current_role","target_role","claimed_skills","marketplace_opt_in"]}
    candidate.patch("/api/profile",json={**update,"marketplace_opt_in":True})
    candidate.post("/api/demo/employer")
    discovered=candidate.get("/api/employer/jobs/demo-python-engineer/candidates").json()
    assert any(c["id"]=="candidate-demo" and c["evidence"][0]["assessment_id"]==new["id"] for c in discovered)
    job=candidate.post("/api/jobs",json={"title":"Python AI Builder","company":"Demo Team","description":"Build reliable AI applications with Python and RAG.","required_skills":["python","rag"]})
    assert job.status_code==200 and job.json()["synthetic"] is True
    candidate.post("/api/demo/candidate")
    candidate.patch("/api/profile",json={**update,"marketplace_opt_in":False})
    candidate.post("/api/demo/employer")
    assert all(c["id"]!="candidate-demo" for c in candidate.get("/api/employer/jobs/demo-python-engineer/candidates").json())
