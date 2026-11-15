from strands import tool
from backend.agents.runtime import run_specialist


def run(service, settings, uid, role, request):
    if role != "candidate":
        raise PermissionError("Only candidates may access their learning roadmap")
    captured = []

    @tool
    def get_learning_plan() -> dict:
        """Compare assessment evidence to job requirements and retrieve prioritized learning milestones."""
        path=service.learning.plan(uid)
        if not path.get('evaluation_id'):
            data={'profile':service.profile(uid),'career_path':path,'assessed_skills':service.skills(uid),
                  'roadmap':{'milestones':[]},'lessons':[], 'evaluation_required':True,
                  'next_action':'Open Learning and choose Evaluate my profile to answer three questions about your skills and goal.'}
            captured.append(data)
            return data
        roadmap = {'target_role':path['target_role'],'note':path.get('summary'),
                   'milestones':[{'skill':s['skill'],'title':s['label'],'status':'completed' if s['mastery']=='foundational' else 'needs_evidence'} for s in path['skills']]}
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
