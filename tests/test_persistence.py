from concurrent.futures import ThreadPoolExecutor
import boto3
from moto import mock_aws
import pytest
from backend.db import MemoryRepository, DynamoRepository, Conflict
from backend.service import Service
from backend.db import item


@pytest.fixture(params=["memory","dynamo"])
def repository(request):
    if request.param=="memory":
        yield MemoryRepository()
    else:
        with mock_aws():
            boto3.client("dynamodb",region_name="us-east-1").create_table(TableName="SkillPilot",
                KeySchema=[{"AttributeName":"PK","KeyType":"HASH"},{"AttributeName":"SK","KeyType":"RANGE"}],
                AttributeDefinitions=[{"AttributeName":"PK","AttributeType":"S"},{"AttributeName":"SK","AttributeType":"S"}],BillingMode="PAY_PER_REQUEST")
            yield DynamoRepository(region="us-east-1")


def test_repository_roundtrip_and_conditional_submission(repository):
    service=Service(repository);service.seed()
    assessment=service.create_assessment("candidate-demo","python")
    result=service.submit("candidate-demo",assessment["id"],{"q1":0,"q2":2,"q3":1,"q4":3})
    reloaded=Service(repository)
    assert reloaded.skills("candidate-demo")[0]["score"]==100
    assert reloaded.assessment("candidate-demo",assessment["id"])["result"]==result["result"]
    assert {m["job"]["id"] for m in reloaded.matches("candidate-demo")}=={j["id"] for j in reloaded.jobs()}
    with pytest.raises(Conflict):
        reloaded.submit("candidate-demo",assessment["id"],{"q1":1,"q2":1,"q3":1,"q4":1})
    assert reloaded.skills("candidate-demo")[0]["score"]==100


def test_memory_concurrent_submission_is_once_only():
    service=Service(MemoryRepository());service.seed()
    a=service.create_assessment("candidate-demo","python")
    def submit():
        try:
            service.submit("candidate-demo",a["id"],{"q1":0,"q2":2,"q3":1,"q4":3})
            return "saved"
        except Conflict:
            return "conflict"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _:submit(),range(2)))==["conflict","saved"]


def test_account_and_session_persist_across_auth_instances(repository):
    from backend.auth import Auth
    from backend.models import SignupRequest, LoginRequest
    from backend.config import Settings
    settings=Settings(seed_accounts=False)
    auth=Auth(Service(repository),settings)
    request=SignupRequest(email="persist@example.com",password="Persistence test password 2026!",name="Persisted User",current_role="Engineer")
    account=auth.signup(request)
    token=auth.create_session(account)
    restored=Auth(Service(repository),settings)
    assert restored.session(token)["uid"]==account["uid"]
    assert restored.login(LoginRequest(email=request.email,password=request.password))["uid"]==account["uid"]
    restored.logout(token)
    from backend.auth import InvalidCredentials
    with pytest.raises(InvalidCredentials):
        auth.session(token)


def test_interview_revision_atomically_guards_profile_updates(repository):
    pk="USER#revision-test"
    repository.write([item(pk,"ONBOARDING#active",{"revision":0}),item(pk,"PROFILE",{"name":"Original"})])
    repository.write([item(pk,"ONBOARDING#active",{"revision":1}),item(pk,"PROFILE",{"name":"Confirmed"})],expected_revision=(pk,"ONBOARDING#active",0))
    with pytest.raises(Conflict):
        repository.write([item(pk,"ONBOARDING#active",{"revision":2}),item(pk,"PROFILE",{"name":"Stale overwrite"})],expected_revision=(pk,"ONBOARDING#active",0))
    assert repository.get(pk,"PROFILE")["name"]=="Confirmed"
    assert repository.get(pk,"ONBOARDING#active")["revision"]==1
