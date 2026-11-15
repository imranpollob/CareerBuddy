from backend.tools.jobs import canonical_skill, skill_label


def match(job, skills):
    # Compare canonical IDs: generated paths and job tags may name one skill differently.
    demonstrated = {canonical_skill(s["skill"]): s for s in skills if s["passed"]}
    supported = [s for s in job["required_skills"] if canonical_skill(s) in demonstrated]
    missing = [s for s in job["required_skills"] if canonical_skill(s) not in demonstrated]
    requirement_label = "listed requirements" if job.get("synthetic", True) else "tracked skill mentions"
    return {"job": job, "supported": supported, "missing": missing,
            "supported_count": len(supported), "required_count": len(job["required_skills"]),
            "evidence": [demonstrated[canonical_skill(s)] for s in supported],
            "explanation": f"{len(supported)} of {len(job['required_skills'])} {requirement_label} supported by fundamentals assessment evidence. "
                           + (f"Still to demonstrate: {', '.join(skill_label(s) for s in missing)}." if missing else "All listed skills have fundamentals evidence; review the full job for experience requirements.")}
