from backend.db import item
from backend.models import ChatResponse


def pass_attempt(client,repo,uid,attempt,*,fail=False):
    key=repo.get(f'USER#{uid}',f"ASSESSMENT_KEY#{attempt['id']}")
    answers={q['id']:(q['correct_index']+1)%4 if fail else q['correct_index'] for q in key['questions']}
    response=client.post(f"/api/assessments/{attempt['id']}/submit",json={'answers':answers})
    assert response.status_code==200,response.text
    return response.json()


def test_competency_progress_only_supports_skill_after_full_path(candidate,repo):
    plan=candidate.post('/api/learning').json()
    skill=plan['skills'][0]['skill']
    expanded=candidate.post(f'/api/learning/{skill}/expand').json()
    path=next(s for s in expanded['skills'] if s['skill']==skill)
    assert len(path['topics'])==3
    for i,topic in enumerate(path['topics']):
        lesson=candidate.get(f"/api/competencies/{topic['id']}/lesson")
        assert lesson.status_code==200 and lesson.json()['examples'] and lesson.json()['key_takeaways']
        attempt=candidate.post(f"/api/competencies/{topic['id']}/practice").json()
        assert attempt['competency_id']==topic['id'] and 'correct_index' not in str(attempt)
        pass_attempt(candidate,repo,'candidate-demo',attempt)
        passport=candidate.get('/api/passport').json()
        assert len(passport['competencies'])==i+1
        if i<2:
            assert not any(e['skill']==skill and e['passed'] for e in passport['skills'])
    result=next(e for e in passport['skills'] if e['skill']==skill)
    assert result['passed'] and result['mastery']=='foundational'
    assert len(result['assessment_ids'])==3
    assert all(e['mastery'] not in {'applied','demonstrated'} for e in passport['skills'])
    assert candidate.get('/api/learning').json()['completed_topics']==3
    retry=candidate.post('/api/assessments',json={'skill':skill,'competency_id':path['topics'][0]['id']}).json()
    pass_attempt(candidate,repo,'candidate-demo',retry,fail=True)
    current=next(e for e in candidate.get('/api/passport').json()['skills'] if e['skill']==skill)
    assert current['passed'] is False and current['mastery']=='not_assessed'
    assert candidate.get('/api/learning').json()['completed_topics']==2


def test_learning_content_is_private_cached_and_goal_scoped(candidate,repo,monkeypatch):
    plan=candidate.post('/api/learning').json();skill=plan['skills'][0]['skill']
    candidate.post(f'/api/learning/{skill}/expand')
    def should_not_generate(*args):
        raise AssertionError('Cached path must be reused')
    monkeypatch.setattr(candidate.app.state.service.intelligence,'skill_path',should_not_generate)
    repeated=candidate.post(f'/api/learning/{skill}/expand')
    assert repeated.status_code==200
    topic=repeated.json()['skills'][0]['topics'][0]
    assert candidate.post('/api/assessments',json={'skill':'unrelated_skill','competency_id':topic['id']}).status_code==400
    candidate.login('student')
    assert candidate.get(f"/api/competencies/{topic['id']}/lesson").status_code==400
    assert candidate.get('/api/passport').json()['competencies']==[]
    candidate.login('employer')
    assert candidate.get('/api/learning').status_code==403
    assert candidate.get('/api/passport').status_code==403


def test_career_purpose_updates_roadmap_without_falsifying_evidence(candidate):
    p=candidate.get('/api/dashboard').json()['profile']
    update={k:p[k] for k in ['name','current_role','target_role','claimed_skills','marketplace_opt_in','career_goal']}
    update.update(career_goal='stay_relevant',target_role='Senior AI Engineer')
    assert candidate.patch('/api/profile',json=update).status_code==200
    plan=candidate.get('/api/learning').json()
    assert plan['career_goal']=='stay_relevant' and plan['target_role']=='Senior AI Engineer'
    assert candidate.get('/api/passport').json()['skills']==[]
    assert candidate.patch('/api/profile',json={**update,'mastery':'demonstrated'}).status_code==422
    assert candidate.patch('/api/profile',json={**update,'career_goal':'invented'}).status_code==422


def test_next_assessment_is_a_saved_roadmap_competency(candidate):
    result=candidate.post('/api/assessments/next')
    assert result.status_code==200,result.text
    attempt=result.json()
    assert attempt['competency_id']
    plan=candidate.get('/api/learning').json()
    assert plan['activity']['assessment_id']==attempt['id']
    assert attempt['competency_id'] in {t['id'] for s in plan['skills'] for t in s['topics']}


def test_saved_conversation_resumes_across_login_and_api_restart(candidate,repo):
    from backend.api import create_app
    from tests.conftest import AccountClient
    candidate.post('/api/chat',json={'message':'Hello, I want to plan my career'})
    history=candidate.get('/api/chat/history').json()
    assert history['revision']==1 and len(history['messages'])==2
    assert history['messages'][0]['role']=='user'
    candidate.post('/api/auth/logout')
    candidate.login('student')
    assert candidate.get('/api/chat/history').json()['messages']==[]
    settings=candidate.app.state.auth.settings
    with AccountClient(create_app(repo,settings)) as restored:
        restored.login('candidate')
        assert restored.get('/api/chat/history').json()==history
    assert 'password' not in str(history) and 'correct_index' not in str(history)


def test_failed_chat_preserves_saved_history(candidate,monkeypatch):
    candidate.post('/api/chat',json={'message':'Hello'})
    before=candidate.get('/api/chat/history').json()
    def unavailable(*args):raise RuntimeError('Model unavailable')
    monkeypatch.setattr('backend.api.chat',unavailable)
    assert candidate.post('/api/chat',json={'message':'Next please'}).status_code==503
    assert candidate.get('/api/chat/history').json()==before


def test_market_refresh_keeps_opened_paths_and_updates_other_focus_slots(candidate,monkeypatch):
    service=candidate.app.state.service
    first=service.learning.start('candidate-demo')['skills'][0]['skill']
    service.learning.expand('candidate-demo',first)
    old_market=service.market
    def changed_market(uid=None):
        market=old_market(uid)
        market['requirements']=[{'skill':'new_market_skill','label':'New market skill','job_count':99,'sources':[]}]+market['requirements']
        return market
    monkeypatch.setattr(service,'market',changed_market)
    refreshed=service.learning.plan('candidate-demo')
    assert refreshed['skills'][0]['skill']==first and refreshed['skills'][0]['expanded']
    assert any(s['skill']=='new_market_skill' for s in refreshed['skills'])
    assert refreshed['total_topics']==3


def test_parallel_topic_submissions_preserve_complete_skill_evidence(candidate,repo):
    from concurrent.futures import ThreadPoolExecutor
    from backend.db import Conflict
    service=candidate.app.state.service;uid='candidate-demo'
    skill=service.learning.start(uid)['skills'][0]['skill']
    topics=service.learning.expand(uid,skill)['skills'][0]['topics']
    attempts=[service.create_assessment(uid,skill,competency_id=t['id']) for t in topics]
    def submit(a):
        key=repo.get(f'USER#{uid}',f"ASSESSMENT_KEY#{a['id']}")
        answers={q['id']:q['correct_index'] for q in key['questions']}
        for _ in range(4):
            try:return service.submit(uid,a['id'],answers)
            except Conflict:continue
        raise AssertionError('Concurrent submission never committed')
    with ThreadPoolExecutor(max_workers=3) as pool:
        assert all(a['status']=='completed' for a in pool.map(submit,attempts))
    evidence=next(e for e in service.skills(uid) if e['skill']==skill)
    assert evidence['passed'] and len(evidence['assessment_ids'])==3
