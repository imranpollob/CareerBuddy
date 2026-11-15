from strands import tool
from backend.agents.runtime import run_specialist


def run(service, settings, uid, role, request):
    captured = []

    @tool
    def analyze_job_requirements() -> dict:
        """Retrieve sourced job postings and deterministic normalized skill frequencies."""
        market = service.market(uid if role == "candidate" else None)
        # Keep agent context compact; full text stays in the repository/API.
        data = {**market, "jobs": [{k: v for k, v in j.items() if k != "description"} for j in market["jobs"]]}
        captured.append(data)
        return data

    return run_specialist(settings, "job_market", "Analyze the provided small job sample. Preserve source references. "
                          "Use Python-computed counts; never generalize sample counts to the entire market.",
                          request, analyze_job_requirements, captured), ["analyze_job_requirements"]
