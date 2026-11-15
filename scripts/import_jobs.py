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
from backend.tools.jobs import extract_skills

BOARDS = {
    "anthropic": ("greenhouse", "Anthropic"), "scaleai": ("greenhouse", "Scale AI"),
    "databricks": ("greenhouse", "Databricks"), "figma": ("greenhouse", "Figma"),
    "hex": ("ashby", "Hex"), "cohere": ("ashby", "Cohere"), "ramp": ("ashby", "Ramp"),
    "perplexity": ("ashby", "Perplexity"), "baseten": ("ashby", "Baseten"),
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
    if re.search(r"manager|director|head of|recruit|account executive", title, re.I):
        return False
    ai = re.search(r"\bAI\b|\bML\b|machine learning|\bLLM\b|research|intelligence", title, re.I)
    engineering = re.search(r"engineer|intern|technical staff", title, re.I)
    early_software = (career_level(title) in {"internship", "entry"} and "engineer" in title.lower()
                      and not re.search(r"security|graphics|database|interaction design", title, re.I)
                      and re.search(r"\bLLM\b|machine learning", content, re.I))
    return bool((ai and engineering) or early_software)


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
                  retrieved_at=datetime.now(timezone.utc).isoformat(), synthetic=False)
        results.append(job.model_dump(mode="json"))
    results.sort(key=lambda j: (j["career_level"] not in {"internship", "entry"}, j["title"]))
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", action="append", choices=BOARDS, help="Repeat to select boards; default all")
    parser.add_argument("--per-board", type=int, default=10, choices=range(1,16))
    parser.add_argument("--minimum-real",type=int,default=50)
    parser.add_argument("--output", default="backend/data/jobs.json")
    args = parser.parse_args()
    path = Path(args.output)
    old = json.loads(path.read_text()) if path.exists() else []
    jobs, failed = [], []
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for board in args.board or BOARDS:
            try:
                found = collect(client, board)[:args.per_board]
                if not found:
                    raise ValueError("No matching postings")
                jobs.extend(found)
                print(f"{BOARDS[board][1]}: {len(found)} sourced postings", flush=True)
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                failed.append(board)
                print(f"{board}: {type(exc).__name__}; retaining prior records for this board", flush=True)
                jobs.extend(j for j in old if not j["synthetic"] and j["company"] == BOARDS[board][1])
    if not any(not j["synthetic"] for j in jobs):
        raise RuntimeError("No public postings available; snapshot unchanged")
    jobs.extend(j for j in old if j["synthetic"])
    jobs = list({j["source_url"] or j["id"]: j for j in jobs}.values())
    if sum(not j["synthetic"] for j in jobs)<args.minimum_real:
        raise RuntimeError("Not enough real jobs returned; existing snapshot left unchanged")
    old_by_url={j["source_url"]:j for j in old if not j["synthetic"]}
    from backend.intelligence import description_hash
    jobs=[old_by_url[j["source_url"]] if j.get("source_url") in old_by_url and old_by_url[j["source_url"]].get("tagging_method")=="llm"
          and description_hash(old_by_url[j["source_url"]])==description_hash(j) else j for j in jobs]
    path.write_text(json.dumps(jobs, indent=2) + "\n")
    write_manifest(path,jobs)
    print(json.dumps({"total": len(jobs), "companies": len({j["company"] for j in jobs if not j["synthetic"]}),
                      "levels": dict(Counter(j["career_level"] for j in jobs)), "failed_boards": failed}))


if __name__ == "__main__":
    main()
