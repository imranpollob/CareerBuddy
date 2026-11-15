"""Owner-scoped text history; no private tool payloads or assessment keys."""
from backend.db import item
from backend.models import ConversationRecord
from backend.service import now


def history(repo,uid):
    return ConversationRecord.model_validate(repo.get(f"USER#{uid}","CHAT#active") or {}).model_dump()


def model_messages(record):
    return [{"role":m["role"],"content":[{"text":m["text"]}]} for m in record["messages"][-12:]]


def append(repo,uid,record,message,response):
    pk,sk=f"USER#{uid}","CHAT#active"
    saved=repo.get(pk,sk)
    data=ConversationRecord(revision=record["revision"]+1,messages=(record["messages"]+[
        {"role":"user","text":message,"created_at":now()},
        {"role":"assistant","text":response.message[:12000],"created_at":now(),"specialists":[d.specialist for d in response.delegations]}])[-24:]).model_dump()
    if saved is None:
        repo.write([item(pk,sk,data)],absent=(pk,sk))
    else:
        repo.write([item(pk,sk,data)],expected_revision=(pk,sk,record["revision"]))
