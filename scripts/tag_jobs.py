"""Analyze saved public postings with Bedrock and save validated skill tags locally.

Runs bounded parallel batches; never creates AWS infrastructure. Each successful
batch is checkpointed so a later retry only processes missing/stale records.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from dotenv import load_dotenv
from backend.config import Settings
from backend.intelligence import Intelligence, description_hash
from backend.models import Job
from scripts.import_jobs import write_manifest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--path",default="backend/data/jobs.json")
    parser.add_argument("--workers",type=int,default=2,choices=[1,2,3])
    parser.add_argument("--force",action="store_true")
    args=parser.parse_args()
    load_dotenv()
    settings=Settings(ai_mode="bedrock")
    ai=Intelligence(settings)
    path=Path(args.path)
    jobs=[Job.model_validate(j).model_dump(mode="json") for j in json.loads(path.read_text())]
    todo=[j for j in jobs if not j["synthetic"] and (args.force or j["tagging_method"]!="llm" or j["tagged_description_hash"]!=description_hash(j))]
    batches=[todo[i:i+4] for i in range(0,len(todo),4)]
    complete,failures=0,[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(ai.tag_jobs,b):b for b in batches}
        for future in as_completed(futures):
            batch=futures[future]
            try:
                tagged=future.result()
            except Exception as exc:
                # Smaller contexts also recover from malformed batch output.
                tagged=[]
                for job in batch:
                    try:
                        tagged.extend(ai.tag_jobs([job]))
                    except Exception as single:
                        failures.append({"id":job["id"],"error":type(single).__name__})
                print(f"Batch retry: {type(exc).__name__}; recovered {len(tagged)}/{len(batch)}",flush=True)
            updated={j["id"]:Job.model_validate(j).model_dump(mode="json") for j in tagged}
            jobs=[updated.get(j["id"],j) for j in jobs]
            complete+=len(tagged)
            temporary=path.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(jobs,indent=2)+"\n")
            temporary.replace(path)
            print(f"Tagged {complete}/{len(todo)} pending public postings",flush=True)
    public=[j for j in jobs if not j["synthetic"]]
    write_manifest(path,jobs)
    report={"real_jobs":len(public),"llm_tagged":sum(j["tagging_method"]=="llm" for j in public),"failures":failures}
    Path(".local").mkdir(exist_ok=True)
    Path(".local/job-tagging-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
    return 0 if not failures and len(public)>=50 else 1


if __name__=="__main__":
    raise SystemExit(main())
