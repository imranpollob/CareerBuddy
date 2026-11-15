from strands import tool
from backend.agents.runtime import run_specialist


def run(service, settings, uid, role, request):
    captured = []

    @tool
    def get_marketplace_matches(job_id: str = "") -> dict:
        """Retrieve candidate job matches or a consenting-candidate preview for an owned employer posting.

        Args:
            job_id: Optional employer posting ID. If empty, retrieve a default posting and list available IDs.
        """
        if role == "candidate":
            matches = service.matches(uid)
            data = {"profile": service.profile(uid), "journey": service.journey(uid),
                    "matches": [{**m, "job": {k: v for k, v in m["job"].items() if k != "description"}} for m in matches[:5]]}
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
                          "Explicitly identify seeded synthetic evidence. Describe gaps as not yet demonstrated, never as proven lack of experience. "
                          "No opaque hiring score, ranking prediction, or inferred personal attributes. Employer data is consent-filtered.",
                          request, get_marketplace_matches, captured), ["get_marketplace_matches"]
