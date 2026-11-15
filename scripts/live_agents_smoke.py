"""Opt-in local inference checks. No infrastructure creation or deployment."""
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

from backend.config import Settings
from backend.db import MemoryRepository
from backend.orchestrator import chat
from backend.service import Service


def main():
    load_dotenv()
    logging.disable(logging.CRITICAL)
    service=Service(MemoryRepository())
    service.seed()
    settings=Settings(ai_mode="bedrock")
    cases=[("What skills are in demand in the saved job postings?", "job_market"),
           ("Prepare a Python assessment.", "assessment"),
           ("Build my learning roadmap based on my assessment evidence.", "coach"),
           ("Find jobs that match my demonstrated skills.", "marketplace")]
    report={"checked_at":datetime.now(timezone.utc).isoformat(),"model_id":settings.model_id,"cases":[]}
    for message,expected in cases:
        try:
            result,_=chat(service,settings,"candidate-demo","candidate",message)
            observed=[d.specialist for d in result.delegations]
            passed=expected in observed and len(observed)<4 and bool(result.message)
            report["cases"].append({"expected":expected,"observed":observed,"passed":passed})
        except Exception as exc:
            report["cases"].append({"expected":expected,"passed":False,"error_type":type(exc).__name__})
        print(json.dumps(report["cases"][-1]),flush=True)
    Path(".local").mkdir(exist_ok=True)
    Path(".local/live-agents-smoke.json").write_text(json.dumps(report,indent=2)+"\n")
    return 0 if all(c["passed"] for c in report["cases"]) else 1


if __name__=="__main__":
    raise SystemExit(main())
