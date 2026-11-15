import pytest
from backend.db import item
from backend.intelligence import GenerationError
from backend.evaluation import Evaluation


def review(client):
    state=client.post('/api/learning/evaluation').json()
    assert state['status']=='interview'
    for index,answer in enumerate(['I am a student. I use Python and SQL and want an AI engineer job.',
                                   'I built a Python API with FastAPI and used SQL to query data.',
                                   'I owned the API and tests. I want to learn LLM application design.']):
        assert state['question_number']==index+1 and state['total_questions']==3
        response=client.post('/api/learning/evaluation/answer',json={'revision':state['revision'],'answer':answer})
        assert response.status_code==200,response.text
        state=response.json()
    assert state['status']=='review'
    return state


def test_dynamic_evaluation_creates_private_versioned_roadmap_and_redo_preserves_evidence(candidate,repo):
    state=review(candidate)
    assert candidate.get('/api/learning').json()['skills']==[]
    assert candidate.post('/api/learning/evaluation/answer',json={'revision':state['revision'],'answer':'fifth question'}).status_code==409
    result=candidate.post('/api/learning/evaluation/complete',json={'revision':state['revision']})
    assert result.status_code==200,result.text
    plan=result.json();first_ids={t['id'] for s in plan['skills'] for t in s['topics']}
    assert plan['evaluation_id']==state['id'] and plan['total_topics']==3
    assert plan['summary'] and candidate.get('/api/dashboard').json()['profile']['claimed_skills']
    assert candidate.post('/api/learning/evaluation/complete',json={'revision':state['revision']}).status_code==409
    topic=plan['next_topic']
    attempt=candidate.post('/api/assessments',json={'skill':topic['skill'],'competency_id':topic['id']}).json()
    key=repo.get('USER#candidate-demo',f"ASSESSMENT_KEY#{attempt['id']}")
    candidate.post(f"/api/assessments/{attempt['id']}/submit",json={'answers':{q['id']:q['correct_index'] for q in key['questions']}})
    before=repo.partition('USER#candidate-demo','ASSESSMENT#')
    evidence=repo.partition('USER#candidate-demo','COMPETENCY#')
    # Begin a redo without losing the current path; reload resumes its revision.
    next_state=review(candidate)
    assert next_state['id']!=state['id']
    assert candidate.get('/api/learning').json()['evaluation_id']==state['id']
    second=candidate.post('/api/learning/evaluation/complete',json={'revision':next_state['revision']}).json()
    assert second['evaluation_id']==next_state['id']
    assert first_ids.isdisjoint({t['id'] for s in second['skills'] for t in s['topics']})
    assert second['completed_topics']==0
    assert repo.partition('USER#candidate-demo','ASSESSMENT#')==before
    assert repo.partition('USER#candidate-demo','COMPETENCY#')==evidence
    assert repo.partition('USER#candidate-demo','PATH_HISTORY#')
    candidate.login('student')
    assert candidate.get('/api/learning/evaluation').json() is None
    assert candidate.get('/api/learning').json()['skills']==[]


def test_evaluation_model_failure_stale_revision_and_unsupported_claims_are_safe(candidate,monkeypatch):
    state=candidate.post('/api/learning/evaluation').json()
    assert candidate.post('/api/learning/evaluation').json()==state
    assert candidate.post('/api/learning/evaluation/answer',json={'revision':999,'answer':'Python'}).status_code==409
    def broken(*args):raise GenerationError('Try again')
    original=candidate.app.state.service.intelligence.interview
    monkeypatch.setattr(candidate.app.state.service.intelligence,'interview',broken)
    assert candidate.post('/api/learning/evaluation/answer',json={'revision':state['revision'],'answer':'Python'}).status_code==503
    assert candidate.get('/api/learning/evaluation').json()==state
    monkeypatch.setattr(candidate.app.state.service.intelligence,'interview',original)
    state=review(candidate)
    monkeypatch.setattr(candidate.app.state.service.intelligence,'roadmap',broken)
    assert candidate.post('/api/learning/evaluation/complete',json={'revision':state['revision']}).status_code==503
    assert candidate.get('/api/learning/evaluation').json()['status']=='review'
    assert candidate.get('/api/learning').json()['skills']==[]
    candidate.login('employer')
    assert candidate.post('/api/learning/evaluation').status_code==403


def test_interview_drives_goal_and_roadmap_order(candidate,monkeypatch):
    from backend.models import GeneratedRoadmap
    state=review(candidate)
    seen=[]
    def choose(profile,messages,requirements,evidence):
        seen.append((profile,messages))
        return GeneratedRoadmap(focus_skills=['sql','python'],summary='Begin with SQL from the interview, then build the Python API skills needed for the goal.')
    monkeypatch.setattr(candidate.app.state.service.intelligence,'roadmap',choose)
    result=candidate.post('/api/learning/evaluation/complete',json={'revision':state['revision']}).json()
    assert [s['skill'] for s in result['skills']]==['sql','python']
    assert 'python' in seen[0][0]['claimed_skills']
    assert len([m for m in seen[0][1] if m['role']=='user'])==3
    assert [s['skill'] for s in candidate.get('/api/learning').json()['skills']]==['sql','python']


def test_evaluation_rejects_ungrounded_skill_claims(candidate,monkeypatch):
    from backend.models import OnboardingTurn
    state=candidate.post('/api/learning/evaluation').json()
    monkeypatch.setattr(candidate.app.state.service.intelligence,'interview',lambda *args:OnboardingTurn(
        question='Which projects have you built?',current_role='Engineer',target_role='AI Engineer',candidate_track='career_switcher',
        ready_to_review=False,claims=[{'skill':'rust','label':'Rust','evidence_excerpt':'I built Rust systems'}]))
    assert candidate.post('/api/learning/evaluation/answer',json={'revision':state['revision'],'answer':'I use Python'}).status_code==400
    assert candidate.get('/api/learning/evaluation').json()==state
    assert candidate.get('/api/passport').json()['skills']==[]


def test_profile_goal_edit_does_not_replace_evaluated_plan_until_redo(candidate):
    state=review(candidate)
    before=candidate.post('/api/learning/evaluation/complete',json={'revision':state['revision']}).json()
    profile=candidate.get('/api/dashboard').json()['profile']
    update={k:profile[k] for k in ['name','current_role','target_role','claimed_skills','marketplace_opt_in','career_goal']}
    update['target_role']='Senior AI Engineer'
    assert candidate.patch('/api/profile',json=update).status_code==200
    after=candidate.get('/api/learning').json()
    assert after['evaluation_id']==before['evaluation_id']
    assert after['target_role']==before['target_role']
    assert after['skills']==before['skills']
