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
        path=service.learning.plan(uid)
        if path["next_topic"] is None:
            missing=next((s for s in path["skills"] if s["mastery"]=="not_assessed" and not s["expanded"]),None)
            if missing:
                path=service.learning.expand(uid,missing["skill"])
        next_steps=[m for m in roadmap["milestones"] if m["status"]!="completed"][:1]
        data = {"profile": service.profile(uid), "journey": service.journey(uid), "roadmap": roadmap, "career_path":path,"assessed_skills": service.skills(uid),
                "lessons": ([service.learning.lesson(uid,path["next_topic"]["id"])] if path["next_topic"] else [service.lesson(uid, m["skill"]) for m in next_steps])}
        captured.append(data)
        return data

    return run_specialist(settings, "coach", "Use assessment-backed evidence and market requirements to explain a learning plan. "
                          "Recommend one actionable lesson and reassessment. Claimed skills are not demonstrated skills.",
                          request, get_learning_plan, captured), ["get_learning_plan"]
