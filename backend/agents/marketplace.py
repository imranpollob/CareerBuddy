from strands import tool
from backend.agents.runtime import run_specialist
from backend.tools.jobs import jobs_for_role


def rank_for_candidate(matches, profile, jobs):
    """Target-role fit first, then career stage, then evidence coverage (same order as the UI)."""
    role_ids = {j["id"] for j in jobs_for_role(jobs, profile.get("target_role", ""))}
    years = profile.get("years_experience")
    early = profile.get("candidate_track") == "student" or (years is not None and years <= 1)
    experienced = years is not None and years >= 3
    def key(m):
        level = m["job"]["career_level"]
        return (m["job"]["id"] not in role_ids,
                early and level not in {"internship", "entry"},
                experienced and level == "internship",
                -m["supported_count"] / max(m["required_count"], 1))
    return [{**m, "fits_target_role": m["job"]["id"] in role_ids} for m in sorted(matches, key=key)]


def run(service, settings, uid, role, request):
    captured = []

    @tool
    def get_marketplace_matches(job_id: str = "") -> dict:
        """Retrieve candidate job matches or a consenting-candidate preview for an owned employer posting.

        Args:
            job_id: Optional employer posting ID. If empty, retrieve a default posting and list available IDs.
        """
        if role == "candidate":
            profile = service.profile(uid)
            ranked = rank_for_candidate(service.matches(uid), profile, service.jobs())
            data = {"profile": profile, "journey": service.journey(uid),
                    "target_role_postings": sum(m["fits_target_role"] for m in ranked),
                    "matches": [{**m, "job": {k: v for k, v in m["job"].items() if k != "description"}} for m in ranked[:5]]}
        else:
            jobs = [j for j in service.jobs() if j.get("employer_id") == uid]
            # Bound repeated evidence in model context; the employer dashboard
            # exposes every owned posting and its complete consenting results.
            jobs.sort(key=lambda j: (j["id"] != "demo-junior-ai", j["title"]))
            selected = [j for j in jobs if j["id"] == job_id] if job_id else jobs[:1]
            if job_id and not selected:
                raise PermissionError("Only your own postings can be used for candidate discovery")
            data = {"available_postings": [{"id": j["id"], "title": j["title"]} for j in jobs],
                    "postings": [{"job": {k: v for k, v in j.items() if k != "description"},
                                  "candidates": service.candidates(uid, j["id"])[:3]} for j in selected],
                    "note": "Focused preview of one owned posting and up to three consenting candidates. Select any posting in the employer dashboard for its full results."}
        captured.append(data)
        return data

    return run_specialist(settings, "marketplace", "Explain requirement coverage using supplied assessment evidence. "
                          "Matches are pre-ranked for this person: recommend postings in the given order and prefer those with fits_target_role true. "
                          "Explicitly identify seeded synthetic evidence. Describe gaps as not yet demonstrated, never as proven lack of experience. "
                          "No opaque hiring score, ranking prediction, or inferred personal attributes. Employer data is consent-filtered.",
                          request, get_marketplace_matches, captured), ["get_marketplace_matches"]
