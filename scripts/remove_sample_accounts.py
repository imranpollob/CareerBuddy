"""Remove only known sample identities and their records from DynamoDB LOCAL.

Never targets AWS or selects users by email/synthetic flags. Signup users have
independent UUIDs and are preserved, including any with matching display names.
"""
import argparse
import json
from pathlib import Path
from backend.db import DynamoRepository


def selected_records(records,user_ids,fixture_jobs):
    job_ids=fixture_jobs|{r["PK"][4:] for r in records if r["SK"]=="DETAILS" and r.get("data",{}).get("employer_id") in user_ids}
    selected=[]
    for record in records:
        data=record.get("data",{})
        if (record["PK"] in {f"USER#{uid}" for uid in user_ids}
            or record["SK"] in {"CREDENTIALS","AUTH_SESSION"} and data.get("uid") in user_ids
            or record["SK"]=="DETAILS" and record["PK"] in {f"JOB#{jid}" for jid in job_ids}
            or record["SK"].startswith("MATCH#") and data.get("job_id") in job_ids):
            selected.append(record)
    return selected


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--endpoint",default="http://127.0.0.1:8001")
    parser.add_argument("--dry-run",action="store_true")
    args=parser.parse_args()
    repo=DynamoRepository(endpoint=args.endpoint,region="us-east-1")
    path=Path(__file__).resolve().parents[1]/"backend"/"data"
    user_ids={f["profile"]["id"] for f in json.loads((path/"demo_profiles.json").read_text())}
    jobs={j["id"] for j in json.loads((path/"jobs.json").read_text()) if j["synthetic"]}
    records=[];params={"ConsistentRead":True}
    while True:
        page=repo.table.scan(**params);records.extend(page["Items"])
        if "LastEvaluatedKey" not in page:break
        params["ExclusiveStartKey"]=page["LastEvaluatedKey"]
    selected=selected_records(records,user_ids,jobs)
    report={"dry_run":args.dry_run,"records":len(selected),"sample_profiles":sum(r["SK"]=="PROFILE" for r in selected),
            "sample_accounts":sum(r["SK"]=="CREDENTIALS" for r in selected),"sample_sessions":sum(r["SK"]=="AUTH_SESSION" for r in selected),
            "sample_jobs":sum(r["SK"]=="DETAILS" for r in selected),
            "signup_profiles_preserved":sum(r["SK"]=="PROFILE" and r["PK"] not in {f"USER#{uid}" for uid in user_ids} for r in records)}
    if not args.dry_run:
        with repo.table.batch_writer() as batch:
            for record in selected:batch.delete_item(Key={"PK":record["PK"],"SK":record["SK"]})
    print(json.dumps(report))


if __name__=="__main__":
    main()
