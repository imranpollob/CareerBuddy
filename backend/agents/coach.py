from strands import tool
from backend.agents.runtime import run_specialist


def run(service, settings, uid, role, request):
    if role != "candidate":
        raise PermissionError("Only candidates may access their learning roadmap")
    captured = []

    @tool
    def get_learning_plan() -> dict:
        """Compare assessment evidence to job requirements and retrieve prioritized learning milestones."""
        roadmap = service.roadmap(uid)
        data = {"profile": service.profile(uid), "journey": service.journey(uid), "roadmap": roadmap, "assessed_skills": service.skills(uid),
                "lessons": [service.lesson(uid, m["skill"]) for m in roadmap["milestones"][:3]]}
        captured.append(data)
        return data

    return run_specialist(settings, "coach", "Use assessment-backed evidence and market requirements to explain a learning plan. "
                          "Recommend one actionable lesson and reassessment. Claimed skills are not demonstrated skills.",
                          request, get_learning_plan, captured), ["get_learning_plan"]
