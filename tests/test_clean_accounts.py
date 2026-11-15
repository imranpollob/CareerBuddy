from fastapi.testclient import TestClient
from backend.api import create_app
from backend.config import Settings
from backend.db import MemoryRepository,item
from backend.service import Service
from scripts.remove_sample_accounts import selected_records


def test_default_startup_has_only_real_jobs_and_no_precreated_accounts(tmp_path):
    repo=MemoryRepository();path=tmp_path/'accounts.json'
    settings=Settings(ai_mode='mock',repository='memory',seed_accounts=False,actor_credentials_path=str(path))
    with TestClient(create_app(repo,settings)) as client:
        assert repo.scan('PROFILE')==[] and repo.scan('CREDENTIALS')==[]
        assert not path.exists()
        signed=client.post('/api/auth/signup',json={'name':'Own account','email':'own@example.com','password':'Own account test password 2026!'})
        assert signed.status_code==200
        uid=signed.json()['profile']['id']
        before=repo.get(f'USER#{uid}','PROFILE')
        client.app.state.service.seed()
        assert repo.get(f'USER#{uid}','PROFILE')==before
        jobs=client.get('/api/jobs').json()
        assert len(jobs)>=50 and all(not j['synthetic'] for j in jobs)
        assert len(repo.scan('PROFILE'))==1


def test_disabled_sample_accounts_cannot_login_or_restore_sessions(repo,tmp_path):
    from backend.auth import Auth,InvalidCredentials,ACTORS,account_key
    import pytest,json
    service=Service(repo);service.seed(include_samples=True)
    enabled=Settings(ai_mode='mock',seed_accounts=True,actor_credentials_path=str(tmp_path/'actors.json'))
    auth=Auth(service,enabled);auth.seed_actors()
    account=repo.get(*account_key(ACTORS['candidate']['email']))
    token=auth.create_session(account)
    disabled=Settings(ai_mode='mock',seed_accounts=False)
    clean=Service(repo,disabled);clean_auth=Auth(clean,disabled)
    with pytest.raises(InvalidCredentials):clean_auth.session(token)
    from backend.models import LoginRequest
    credentials=json.loads((tmp_path/'actors.json').read_text())['candidate']
    with pytest.raises(InvalidCredentials):clean_auth.login(LoginRequest(**credentials))
    assert all(not j['synthetic'] for j in clean.jobs())
    assert clean.candidates('employer-demo','demo-ai-engineer')==[]


def test_cleanup_selects_only_known_fixture_users_and_their_derived_records():
    rows=[item('USER#candidate-demo','PROFILE',{'id':'candidate-demo'}),
          item('USER#candidate-demo','ASSESSMENT#a',{'id':'a'}),
          item('ACCOUNT#sample','CREDENTIALS',{'uid':'candidate-demo'}),
          item('SESSION#sample','AUTH_SESSION',{'uid':'candidate-demo'}),
          item('JOB#sample-job','DETAILS',{}),
          item('JOB#sample-created','DETAILS',{'employer_id':'employer-demo'}),
          item('USER#real','MATCH#sample-job',{'job_id':'sample-job'}),
          item('USER#real','PROFILE',{'id':'real','name':'Alex Morgan'}),
          item('USER#real','ASSESSMENT#own',{'id':'own'}),
          item('ACCOUNT#real','CREDENTIALS',{'uid':'real'}),
          item('SESSION#real','AUTH_SESSION',{'uid':'real'}),
          item('JOB#real','DETAILS',{'employer_id':'real'})]
    selected=selected_records(rows,{'candidate-demo','employer-demo'},{'sample-job'})
    assert len(selected)==7
    assert all(r not in selected for r in rows[7:])


def test_new_account_reads_stay_empty_and_creation_is_private(client,repo,monkeypatch):
    from backend.intelligence import GenerationError
    signed=client.post('/api/auth/signup',json={'name':'Fresh','email':'fresh@example.com','password':'Fresh account password 2026!'})
    uid=signed.json()['profile']['id'];pk=f'USER#{uid}'
    # A legacy shortlist created by old GET requests must not appear as a plan.
    repo.write([item(pk,'CAREER_PATH#active',{'goal':{k:signed.json()['profile'][k] for k in ['current_role','target_role','career_goal']},'focus_skills':['python']})])
    for _ in range(2):
        plan=client.get('/api/learning').json()
        assert plan['skills']==[] and plan['total_topics']==0
        assert client.get('/api/passport').json()['assessments']==[]
    def unavailable(*args):raise GenerationError('Unavailable')
    ai=client.app.state.service.intelligence
    original=ai.skill_path
    monkeypatch.setattr(ai,'skill_path',unavailable)
    assert client.post('/api/learning').status_code==503
    assert client.get('/api/learning').json()['skills']==[]
    monkeypatch.setattr(ai,'skill_path',original)
    assert client.post('/api/learning').json()['total_topics']==3
    client.login('student')
    assert client.get('/api/learning').json()['skills']==[]
    assert client.get('/api/passport').json()['assessments']==[]
