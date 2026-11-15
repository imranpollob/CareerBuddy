from copy import deepcopy
from backend.db import item
from backend.service import Service
from scripts.import_jobs import career_level


def test_student_identity_and_profile_isolation(candidate):
    engineer = candidate.get("/api/dashboard").json()
    assert engineer["profile"]["candidate_track"]=="career_switcher"
    candidate.login("student")
    student = candidate.get("/api/dashboard").json()
    assert student["profile"]["id"]=="student-demo"
    assert student["profile"]["current_role"]=="Computer Science Student"
    assert student["profile"]["role"]=="candidate"
    assert student["journey"]["title"]==student["profile"]["target_role"]
    assert len(student["market"]["jobs"])>=50
    assert student["profile"]["current_role"]=="Computer Science Student"
    attempt=candidate.post("/api/assessments",json={"skill":"python"}).json()
    candidate.post(f"/api/assessments/{attempt['id']}/submit",json={"answers":{"q1":0,"q2":2,"q3":1,"q4":3}})
    assert candidate.get("/api/dashboard").json()["skills"][0]["synthetic"] is False
    candidate.login("candidate")
    assert candidate.get(f"/api/assessments/{attempt['id']}").status_code==400
    assert candidate.get("/api/dashboard").json()["skills"]==[]
    candidate.login("student")
    assert candidate.get("/api/dashboard").json()["skills"][0]["assessment_id"]==attempt["id"]


def test_student_learning_to_employer_with_consent(candidate):
    candidate.login("student")
    before=candidate.get("/api/matches").json()
    assert len(before)>=50
    attempt=candidate.post("/api/lessons/python/complete").json()
    assert candidate.get("/api/dashboard").json()["skills"]==[]
    candidate.post(f"/api/assessments/{attempt['id']}/submit",json={"answers":{"q1":0,"q2":2,"q3":1,"q4":3}})
    matches=candidate.get("/api/matches").json()
    assert next(m for m in matches if m["job"]["id"]=="demo-junior-ai")["supported_count"]==1
    profile=candidate.get("/api/dashboard").json()["profile"]
    update={k:profile[k] for k in ["name","current_role","target_role","claimed_skills","marketplace_opt_in"]}
    assert candidate.patch("/api/profile",json={**update,"candidate_track":"experienced"}).status_code==422
    candidate.login("employer")
    assert all(c["id"]!="student-demo" for c in candidate.get("/api/employer/jobs/demo-junior-ai/candidates").json())
    candidate.login("student")
    candidate.patch("/api/profile",json={**update,"marketplace_opt_in":True})
    candidate.login("employer")
    found=candidate.get("/api/employer/jobs/demo-junior-ai/candidates").json()
    student=next(c for c in found if c["id"]=="student-demo")
    assert student["candidate_track"]=="student"
    assert student["evidence"][0]["synthetic"] is False
    assert "answers" not in student
    assert all(c["id"]!="seed-private" for c in found)


def test_seed_upgrade_preserves_edits_consent_and_evidence(repo):
    service=Service(repo);service.seed(include_samples=True)
    profile=service.profile("student-demo")
    profile.update(name="Edited student",marketplace_opt_in=True)
    repo.write([item("USER#student-demo","PROFILE",profile)])
    a=service.create_assessment("student-demo","sql")
    service.submit("student-demo",a["id"],{"q1":0,"q2":0,"q3":1,"q4":0})
    evidence=deepcopy(service.skills("student-demo"))
    service.seed(include_samples=True)
    assert service.profile("student-demo")["name"]=="Edited student"
    assert service.profile("student-demo")["marketplace_opt_in"] is True
    assert service.skills("student-demo")==evidence


def test_data_covers_students_and_engineers(repo):
    service=Service(repo);service.seed(include_samples=True)
    jobs=service.jobs()
    public=[j for j in jobs if not j["synthetic"]]
    assert len(public)>=50
    assert len({j["source_url"] for j in public})==len(public)
    from backend.intelligence import normalized_text, description_hash
    for job in public:
        assert job["tagging_method"]=="llm" and job["tagging_model"]
        assert job["tagged_description_hash"]==description_hash(job)
        assert job["skill_tags"]
        assert all(normalized_text(t["evidence_excerpt"]) in normalized_text(job["description"]) for t in job["skill_tags"])
    assert len({j["company"] for j in public})>=5
    assert sum(j["career_level"] in {"entry","internship"} for j in public)>=5
    assert all(j["source_url"] and j["retrieved_at"] for j in public)
    assert career_level("AI Engineer, Internal Tools")=="unspecified"
    assert career_level("Senior Engineer - Database Internals")=="senior"
    assert career_level("AI Engineer Intern")=="internship"
    assert career_level("Member of Technical Staff (Early Career)")=="entry"


def test_employer_chat_uses_consent_filtered_preview(client):
    client.login("employer")
    response=client.post("/api/chat",json={"message":"Find candidates for my AI engineer jobs"})
    assert response.status_code==200
    delegation=response.json()["delegations"][0]
    assert delegation["specialist"]=="marketplace"
    data=delegation["result"]["data"]
    assert len(data["postings"])==1
    assert data["postings"][0]["job"]["employer_id"]=="employer-demo"
    assert {c["id"] for c in data["postings"][0]["candidates"]}=={"seed-candidate","seed-switcher","seed-student"}
    assert all(e["synthetic"] for c in data["postings"][0]["candidates"] for e in c["evidence"])
