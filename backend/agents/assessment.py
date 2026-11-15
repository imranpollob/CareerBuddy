from strands import tool
from backend.agents.runtime import run_specialist


def run(service, settings, uid, role, request):
    if role != "candidate":
        raise PermissionError("Only candidates may create their own assessments")
    captured = []

    @tool
    def prepare_skill_assessment(skill: str = "") -> dict:
        """Generate a personalized four-question assessment for a normalized skill identified in the profile or job sample.

        Args:
            skill: A requested normalized skill; leave empty for the next roadmap competency.
        """
        data = service.create_assessment(uid, skill) if skill else service.learning.next_assessment(uid)
        captured.append(data)
        return data

    return run_specialist(settings, "assessment", "Prepare a short fundamentals assessment using your tool. "
                          "Objective grading occurs only on authenticated form submission. Never assign results from claims or chat.",
                          request, prepare_skill_assessment, captured), ["prepare_skill_assessment"]
