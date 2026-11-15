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
        response=client.post('/api/learning/evaluation/answer',json={'revision':state['revision'],'answer':answer,'target_role':'AI Engineer','career_goal':'find_job'})
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
    assert candidate.post('/api/learning/evaluation/answer',json={'revision':999,'answer':'Python','target_role':'AI Engineer','career_goal':'find_job'}).status_code==409
    def broken(*args):raise GenerationError('Try again')
    original=candidate.app.state.service.intelligence.interview
    monkeypatch.setattr(candidate.app.state.service.intelligence,'interview',broken)
    assert candidate.post('/api/learning/evaluation/answer',json={'revision':state['revision'],'answer':'Python','target_role':'AI Engineer','career_goal':'find_job'}).status_code==503
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
    assert candidate.post('/api/learning/evaluation/answer',json={'revision':state['revision'],'answer':'I use Python','target_role':'AI Engineer','career_goal':'find_job'}).status_code==400
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


def test_signup_and_background_never_invent_goal_and_first_evaluation_collects_it(client,monkeypatch,repo):
    signed=client.post('/api/auth/signup',json={'name':'New person','email':'no-goal@example.com','password':'A long test password 2026!'})
    profile=signed.json()['profile'];uid=profile['id']
    assert profile['target_role']=='' and profile['career_goal']=='unspecified'
    assert profile['candidate_track']=='unspecified' and profile['current_role']==''
    state=client.get('/api/onboarding').json()
    for answer in ['Student','Bachelor’s degree','0','Beginner']:
        state=client.post('/api/onboarding/answer',json={'revision':state['revision'],'answer':answer}).json()
    profile=client.post('/api/onboarding/complete',json={'revision':state['revision']}).json()
    assert profile['current_role']=='Student' and profile['target_role']=='' and profile['career_goal']=='unspecified'
    def should_not_infer(*args):raise AssertionError('No model needed before an explicit goal')
    monkeypatch.setattr(client.app.state.service.intelligence,'interview',should_not_infer)
    evaluation=client.post('/api/learning/evaluation').json()
    assert 'AI Engineer' not in evaluation['question'] and evaluation['target_role']==''
    assert client.post('/api/learning/evaluation/answer',json={'revision':evaluation['revision'],'answer':'I use Python'}).status_code==400
    assert client.post('/api/assessments',json={}).status_code==422
    assert client.get('/api/dashboard').json()['journey']['title']=='Choose your career direction'
    # Legacy automatic values are not exposed as confirmed intent or overwritten in storage.
    raw=repo.get(f'USER#{uid}','PROFILE');raw.update(target_role='AI Engineer',career_goal='switch_careers',candidate_track='career_switcher')
    repo.write([item(f'USER#{uid}','PROFILE',raw)])
    assert client.get('/api/session').json()['profile']['target_role']==''
    assert repo.get(f'USER#{uid}','PROFILE')['target_role']=='AI Engineer'


def test_writer_roadmap_accepts_new_skills_without_borrowing_ai_market_claims(candidate,monkeypatch):
    from backend.models import GeneratedRoadmap
    from backend.tools.jobs import jobs_for_role
    assert jobs_for_role(candidate.app.state.service.jobs(),'writer')==[]
    state=candidate.post('/api/learning/evaluation').json()
    for answer in ['I am a student and want to write short stories.','I write essays for school.','I want to improve narrative structure and editing.']:
        state=candidate.post('/api/learning/evaluation/answer',json={'revision':state['revision'],'answer':answer,
            'target_role':'Writer','career_goal':'switch_careers'}).json()
    ai=candidate.app.state.service.intelligence
    def writing_roadmap(profile,messages,requirements,evidence):
        assert profile['target_role']=='Writer' and requirements==[]
        return GeneratedRoadmap(focus_skills=['Narrative Structure','Editing'],summary='Practice narrative structure and editing based on your writing goal and interview.')
    monkeypatch.setattr(ai,'roadmap',writing_roadmap)
    response=candidate.post('/api/learning/evaluation/complete',json={'revision':state['revision']})
    assert response.status_code==200,response.text
    plan=response.json()
    assert plan['target_role']=='Writer' and not plan['market_role_covered']
    assert [s['skill'] for s in plan['skills']]==['narrative_structure','editing']
    assert all(s['job_count']==0 for s in plan['skills'])
    assert plan['total_topics']==3
    assert candidate.post('/api/learning/editing/expand').status_code==200
    topic=plan['next_topic']
    assert candidate.get(f"/api/competencies/{topic['id']}/lesson").status_code==200
    attempt=candidate.post('/api/assessments',json={'skill':topic['skill'],'competency_id':topic['id']})
    assert attempt.status_code==200 and len(attempt.json()['questions'])==4
    assert candidate.get('/api/learning').json()['target_role']=='Writer'


def test_general_roadmap_still_validates_skill_ids():
    from backend.models import GeneratedRoadmap
    from pydantic import ValidationError
    with pytest.raises(ValidationError):GeneratedRoadmap(focus_skills=['../arbitrary-path'],summary='A sufficiently long explanation.')
    # Duplicates and qualifier variants collapse to one canonical skill instead of failing generation.
    assert GeneratedRoadmap(focus_skills=['Editing','editing'],summary='A sufficiently long explanation.').focus_skills==['editing']
    assert GeneratedRoadmap(focus_skills=['performance_optimization','web_performance_optimization'],summary='A sufficiently long explanation.').focus_skills==['performance_optimization']


def test_job_evidence_matches_skill_id_variants():
    from backend.tools.matching import match
    from backend.tools.jobs import canonical_skill
    assert canonical_skill('web_performance_optimization')=='performance_optimization'
    assert canonical_skill('playwright_testing')==canonical_skill('playwright')=='playwright'
    assert canonical_skill('python_testing')=='python_testing'  # unrelated compounds stay distinct
    job={'required_skills':['web_performance_optimization','playwright','react'],'synthetic':False}
    evidence=[{'skill':'performance_optimization','passed':True},{'skill':'playwright_testing','passed':True}]
    result=match(job,evidence)
    assert result['supported']==['web_performance_optimization','playwright'] and result['missing']==['react']
    assert 'Still to demonstrate: React.' in result['explanation']


def test_claim_label_names_the_skill():
    from backend.models import SkillClaim
    claim=SkillClaim(skill='react',label='used in project',evidence_excerpt='I built it in React')
    assert claim.label=='React'
    assert SkillClaim(skill='storybook',label='Storybook',evidence_excerpt='with Storybook').label=='Storybook'


def test_blank_signup_name_is_a_clear_error(client):
    response=client.post('/api/auth/signup',json={'name':'   ','email':'blank@example.com','password':'long-enough-pw','role':'candidate'})
    assert response.status_code==422
    assert 'pydantic' not in response.text and 'Enter your name.' in response.text
