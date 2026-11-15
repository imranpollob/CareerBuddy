"""Verify real DynamoDB Local reads, transactions and reloading with a demo-only user."""
from backend.db import DynamoRepository, item, Conflict
from backend.models import Profile
from backend.service import Service


def main():
    repo=DynamoRepository(endpoint="http://127.0.0.1:8001",region="us-east-1")
    service=Service(repo)
    service.seed()
    uid="local-smoke"
    profile=Profile(id=uid,role="candidate",name="Local persistence check",current_role="Engineer",
                    target_role="AI Engineer",claimed_skills=["python"],marketplace_opt_in=False)
    repo.write([item(f"USER#{uid}","PROFILE",profile.model_dump())])
    attempt=service.create_assessment(uid,"python")
    service.submit(uid,attempt["id"],{"q1":0,"q2":2,"q3":1,"q4":3})
    reloaded=Service(DynamoRepository(endpoint="http://127.0.0.1:8001",region="us-east-1"))
    assert reloaded.skills(uid)[0]["score"]==100
    assert reloaded.assessment(uid,attempt["id"])["status"]=="completed"
    try:
        reloaded.submit(uid,attempt["id"],{"q1":1,"q2":1,"q3":1,"q4":1})
        raise AssertionError("Duplicate submission accepted")
    except Conflict:
        pass
    assert len(reloaded.matches(uid))>=12
    print("DynamoDB Local: seeded, graded atomically, reloaded evidence, rejected replay, and matched jobs")


if __name__=="__main__":
    main()
