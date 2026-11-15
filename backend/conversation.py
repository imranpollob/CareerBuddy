"""Owner-scoped text history; no private tool payloads or assessment keys."""
from backend.db import item
from backend.models import ConversationRecord
from backend.service import now


def history(repo,uid):
    return ConversationRecord.model_validate(repo.get(f"USER#{uid}","CHAT#active") or {}).model_dump()


def model_messages(record):
    return [{"role":m["role"],"content":[{"text":m["text"]}]} for m in record["messages"][-12:]]


def clear(repo,uid):
    """Start a new conversation. Learning, assessments and evidence are untouched.
    The revision moves forward so a reply still in flight cannot overwrite the reset."""
    pk,sk=f"USER#{uid}","CHAT#active"
    record=history(repo,uid)
    data=ConversationRecord(revision=record["revision"]+1,messages=[]).model_dump()
    if repo.get(pk,sk) is None:
        repo.write([item(pk,sk,data)],absent=(pk,sk))
    else:
        repo.write([item(pk,sk,data)],expected_revision=(pk,sk,record["revision"]))
    return data


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
