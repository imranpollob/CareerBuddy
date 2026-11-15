from backend.models import OnboardingTurn
from backend.db import item


def new_candidate(client):
    response=client.post("/api/auth/signup",json={"name":"New Candidate","email":"adaptive@example.com","password":"Adaptive account password 2026!"})
    assert response.status_code==200
    assert response.json()["profile"]["onboarding_completed"] is False
    return response.json()["profile"]["id"]


def test_simple_signup_adaptive_onboarding_and_generated_assessment(client,repo):
    uid=new_candidate(client)
    state=client.get("/api/onboarding").json()
    assert state["revision"]==0 and state["status"]=="interview"
    answers=['Computer science student',"Bachelor’s degree",'0','Beginner']
    for revision,answer in enumerate(answers):
        assert state['question_number']==revision+1
        assert state['total_questions']==4
        if revision:
            assert client.post('/api/onboarding/answer',json={'revision':0,'answer':answer}).status_code==409
        response=client.post('/api/onboarding/answer',json={'revision':revision,'answer':answer})
        assert response.status_code==200
        state=response.json()
    assert state['status']=='review' and state['claims']==[]
    assert client.post('/api/onboarding/answer',json={'revision':4,'answer':'Extra'}).status_code==409
    assert client.get('/api/dashboard').json()['skills']==[]
    profile=client.post('/api/onboarding/complete',json={'revision':4}).json()
    assert profile['onboarding_completed'] and profile['candidate_track']=='student'
    assert profile['education_level']=="Bachelor’s degree" and profile['years_experience']==0
    assert profile['expertise_level']=='Beginner' and profile['claimed_skills']==[]
    assessment=client.post("/api/assessments",json={"skill":"fastapi"}).json()
    assert assessment["kind"]=="mock_generated_v1"
    assert len(assessment["questions"])==4
    assert all("correct_index" not in q and "explanation" not in q for q in assessment["questions"])
    assert "correct_index" not in client.get("/api/dashboard").text
    key=repo.get(f"USER#{uid}",f"ASSESSMENT_KEY#{assessment['id']}")
    assert key and len(key["questions"])==4
    answers={q["id"]:q["correct_index"] for q in key["questions"]}
    result=client.post(f"/api/assessments/{assessment['id']}/submit",json={"answers":answers}).json()
    assert result["result"]["score"]==100
    assert client.post(f"/api/assessments/{assessment['id']}/submit",json={"answers":answers}).status_code==409


def test_onboarding_validates_options_and_never_writes_scores(client):
    new_candidate(client)
    client.get('/api/onboarding')
    assert client.post('/api/onboarding/complete',json={'revision':0}).status_code==409
    client.post('/api/onboarding/answer',json={'revision':0,'answer':'Engineer'})
    for answer in ['Made up degree','Expert','31']:
        assert client.post('/api/onboarding/answer',json={'revision':1,'answer':answer}).status_code==400
    assert client.get('/api/onboarding').json()['revision']==1
    assert client.get('/api/dashboard').json()['skills']==[]


def test_generated_grading_is_immutable_after_profile_changes(candidate,repo):
    a=candidate.post("/api/assessments",json={"skill":"typescript"}).json()
    assert a["kind"]=="mock_generated_v1"
    data=candidate.get("/api/dashboard").json()
    update={k:data["profile"][k] for k in ["name","current_role","target_role","claimed_skills","marketplace_opt_in"]}
    update["claimed_skills"]=["typescript"]
    candidate.patch("/api/profile",json=update)
    assert candidate.get("/api/dashboard").json()["skills"]==[]
    assert candidate.post(f"/api/assessments/{a['id']}/submit",json={"answers":{"q1":0,"q2":0,"q3":0,"q4":0},"score":100}).status_code==422


def test_job_tags_require_actual_source_excerpts(client,monkeypatch):
    from backend.intelligence import Intelligence
    from backend.config import Settings
    from backend.models import TaggedPostings
    ai=Intelligence(Settings(ai_mode="bedrock"))
    generated=TaggedPostings(postings=[{"job_id":"test","tags":[
        {"skill":"python","label":"Python","requirement":"required","evidence_excerpt":"Build Python services"},
        {"skill":"rust","label":"Rust","requirement":"preferred","evidence_excerpt":"Rust production experience"}]}])
    monkeypatch.setattr(ai,"generate",lambda *args:generated)
    job={"id":"test","title":"AI Engineer","description":"Build Python services for AI applications.","required_skills":["python"]}
    tagged=ai.tag_jobs([job])[0]
    assert [t["skill"] for t in tagged["skill_tags"]]==["python"]
    assert tagged["tagging_method"]=="llm" and tagged["tagged_description_hash"]


def test_generation_failure_preserves_interview_and_creates_no_attempt(candidate,repo,monkeypatch):
    from backend.intelligence import GenerationError
    def unavailable(*args):
        raise GenerationError("AI service unavailable; please retry")
    monkeypatch.setattr(candidate.app.state.service.intelligence,"assessment",unavailable)
    assert candidate.post("/api/assessments",json={"skill":"fastapi"}).status_code==503
    assert repo.partition("USER#candidate-demo","ASSESSMENT#")==[]
    assert repo.partition("USER#candidate-demo","ASSESSMENT_KEY#")==[]
    new_candidate(candidate)
    # Background questions work even when the model is unavailable.
    monkeypatch.setattr(candidate.app.state.service.intelligence,'interview',unavailable)
    assert candidate.post('/api/onboarding/answer',json={'revision':0,'answer':'Software engineer'}).status_code==200


def test_private_interview_labels_do_not_leak_to_other_accounts(candidate,repo):
    service=candidate.app.state.service
    repo.write([item("USER#candidate-demo","ONBOARDING#active",{"claims":[
        {"skill":"private_framework","label":"Private project framework","evidence_excerpt":"My private framework"}]}),
        item("CATALOG#private_framework","SKILL",{"skill":"private_framework","label":"Legacy private label"})])
    assert service.catalog("candidate-demo")["private_framework"]=="Private project framework"
    assert "private_framework" not in service.catalog("student-demo")
