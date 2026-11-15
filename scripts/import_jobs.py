"""Collect a bounded, attributed AI/ML sample from public employer boards.

No AWS calls. Retain synthetic demo jobs and preserve sources on API failures.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from html import unescape
import json
from pathlib import Path
import re
import httpx
from backend.models import Job
from backend.tools.jobs import extract_skills, role_family

BOARDS = {
    "anthropic": ("greenhouse", "Anthropic"), "scaleai": ("greenhouse", "Scale AI"),
    "databricks": ("greenhouse", "Databricks"), "figma": ("greenhouse", "Figma"),
    "hex": ("ashby", "Hex"), "cohere": ("ashby", "Cohere"), "ramp": ("ashby", "Ramp"),
    "perplexity": ("ashby", "Perplexity"), "baseten": ("ashby", "Baseten"),
    # Broad computer-science employers: web, mobile, backend, data, infrastructure and security roles.
    "stripe": ("greenhouse", "Stripe"), "airbnb": ("greenhouse", "Airbnb"), "cloudflare": ("greenhouse", "Cloudflare"),
    "datadog": ("greenhouse", "Datadog"), "discord": ("greenhouse", "Discord"), "dropbox": ("greenhouse", "Dropbox"),
    "robinhood": ("greenhouse", "Robinhood"), "lyft": ("greenhouse", "Lyft"), "pinterest": ("greenhouse", "Pinterest"),
    "reddit": ("greenhouse", "Reddit"), "duolingo": ("greenhouse", "Duolingo"), "coinbase": ("greenhouse", "Coinbase"),
    "mongodb": ("greenhouse", "MongoDB"), "notion": ("ashby", "Notion"), "plaid": ("ashby", "Plaid"),
    "supabase": ("ashby", "Supabase"),
}


def write_manifest(path, jobs):
    public=[j for j in jobs if not j["synthetic"]]
    tags=[t for j in public for t in j.get("skill_tags",[])]
    manifest={"real_postings":len(public),"synthetic_postings":len(jobs)-len(public),
              "employers":dict(Counter(j["company"] for j in public)),
              "career_levels":dict(Counter(j["career_level"] for j in public)),
              "llm_tagged_postings":sum(j.get("tagging_method")=="llm" for j in public),
              "source_grounded_skill_tags":len(tags),"distinct_tagged_skills":len({t["skill"] for t in tags}),
              "tagging_models":sorted({j["tagging_model"] for j in public if j.get("tagging_model")}),
              "latest_tagged_at":max((j["tagged_at"] for j in public if j.get("tagged_at")),default=None),
              "source_apis":["Greenhouse public Job Board API","Ashby public Job Postings API"]}
    path.with_name(path.stem+"_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")


def career_level(title):
    if re.search(r"\bintern(ship)?\b|co-op", title, re.I):
        return "internship"
    if re.search(r"new grad|early career|university grad|graduate|\bjunior\b|entry.level", title, re.I):
        return "entry"
    if re.search(r"\bsenior\b|\bstaff\b|\bprincipal\b|\bsr\.", title, re.I) and "technical staff" not in title.lower():
        return "senior"
    return "unspecified"


def relevant(title, content):
    """Any computer-science engineering/data role; the family drives balanced sampling."""
    return role_family(title) is not None


def collect(client, board):
    provider, company = BOARDS[board]
    url = (f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true" if provider == "greenhouse"
           else f"https://api.ashbyhq.com/posting-api/job-board/{board}")
    response = client.get(url)
    response.raise_for_status()
    results = []
    for raw in response.json()["jobs"]:
        if raw.get("isListed") is False:
            continue
        title = raw["title"].strip()
        content = raw.get("content", "") if provider == "greenhouse" else raw.get("descriptionPlain", "") or raw.get("descriptionHtml", "")
        content = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(content))).strip()
        if not relevant(title, content):
            continue
        skills = extract_skills(content)
        if not skills:
            continue
        location = raw["location"]["name"] if provider == "greenhouse" else raw.get("location", "See posting")
        source_url = raw["absolute_url"] if provider == "greenhouse" else raw["jobUrl"]
        job = Job(id=f"{provider}-{board}-{raw['id']}", title=title[:120], company=company, location=location[:100],
                  description=content[:12000], required_skills=skills, career_level=career_level(title),
                  source_url=source_url, source_name=f"{provider.title()} / {company} (keyword-extracted skills)",
                  retrieved_at=datetime.now(timezone.utc).isoformat(), synthetic=False, role_family=role_family(title))
        results.append(job.model_dump(mode="json"))
    results.sort(key=lambda j: (j["career_level"] not in {"internship", "entry"}, j["title"]))
    return results


def balanced(candidates, per_family, per_board_family, family_caps=None):
    """Spread the sample across role families and employers; early-career postings first."""
    by_family = {}
    for job in candidates:
        by_family.setdefault(job["role_family"], []).append(job)
    chosen = []
    for family, jobs in by_family.items():
        cap, board_cap = (family_caps or {}).get(family, (per_family, per_board_family))
        jobs.sort(key=lambda j: (j["career_level"] not in {"internship", "entry"}, j["company"], j["title"]))
        taken, per_board = [], Counter()
        # Round-robin by employer so one large board cannot fill a family.
        while len(taken) < cap:
            progressed = False
            for company in sorted({j["company"] for j in jobs}):
                job = next((j for j in jobs if j["company"] == company and j not in taken), None)
                if job and per_board[company] < board_cap and len(taken) < cap:
                    taken.append(job); per_board[company] += 1; progressed = True
            if not progressed:
                break
        chosen.extend(taken)
    return chosen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", action="append", choices=BOARDS, help="Repeat to select boards; default all")
    parser.add_argument("--per-family", type=int, default=16, choices=range(1,41))
    parser.add_argument("--per-board-family", type=int, default=3, choices=range(1,11))
    parser.add_argument("--ai-family", type=int, default=36, choices=range(1,81))
    parser.add_argument("--minimum-real",type=int,default=50)
    parser.add_argument("--output", default="backend/data/jobs.json")
    args = parser.parse_args()
    path = Path(args.output)
    old = json.loads(path.read_text()) if path.exists() else []
    found_all, failed = [], []
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for board in args.board or BOARDS:
            try:
                found = collect(client, board)
                if not found:
                    raise ValueError("No matching postings")
                found_all.extend(found)
                print(f"{BOARDS[board][1]}: {len(found)} relevant postings", flush=True)
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                failed.append(board)
                print(f"{board}: {type(exc).__name__}; retaining prior records for this board", flush=True)
                found_all.extend({**j, "role_family": j.get("role_family") or role_family(j["title"])}
                                 for j in old if not j["synthetic"] and j["company"] == BOARDS[board][1])
    # AI/ML roles are the core demo audience, so that family gets a deeper sample.
    family_caps = {"ml_ai": (args.ai_family, 5)}
    jobs = balanced(found_all, args.per_family, args.per_board_family, family_caps)
    print("Role families:", dict(Counter(j["role_family"] for j in jobs)), flush=True)
    if not any(not j["synthetic"] for j in jobs):
        raise RuntimeError("No public postings available; snapshot unchanged")
    jobs.extend(j for j in old if j["synthetic"])
    jobs = list({j["source_url"] or j["id"]: j for j in jobs}.values())
    if sum(not j["synthetic"] for j in jobs)<args.minimum_real:
        raise RuntimeError("Not enough real jobs returned; existing snapshot left unchanged")
    old_by_url={j["source_url"]:j for j in old if not j["synthetic"]}
    from backend.intelligence import description_hash
    jobs=[{**old_by_url[j["source_url"]],"role_family":j["role_family"]} if j.get("source_url") in old_by_url and old_by_url[j["source_url"]].get("tagging_method")=="llm"
          and description_hash(old_by_url[j["source_url"]])==description_hash(j) else j for j in jobs]
    path.write_text(json.dumps(jobs, indent=2) + "\n")
    write_manifest(path,jobs)
    print(json.dumps({"total": len(jobs), "companies": len({j["company"] for j in jobs if not j["synthetic"]}),
                      "levels": dict(Counter(j["career_level"] for j in jobs)), "failed_boards": failed}))


if __name__ == "__main__":
    main()
