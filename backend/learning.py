"""One saved career path, with private competency content and derived evidence."""
from backend.db import item, Conflict
from backend.tools.jobs import normalize_skills, skill_label
from backend.models import LearningRecord, PassportRecord, SkillEvidence


class Learning:
    def __init__(self,service):
        self.service,self.repo=service,service.repo

    def plan(self,uid,*,preview=False):
        profile=self.service.profile(uid)
        pk=f"USER#{uid}"
        market=self.service.market(uid)["requirements"]
        if profile["candidate_track"]=="student":
            order={"python":0,"sql":1,"llm":2}
            market.sort(key=lambda r:(order.get(r["skill"],3),-r["job_count"]))
        goal={k:profile[k] for k in ["current_role","target_role","career_goal"]}
        saved=self.repo.get(pk,"CAREER_PATH#active")
        # Older page loads saved generic shortlists. They are not user-created plans.
        started = bool(saved and (saved.get('requested') or self.repo.partition(pk,'PATH#')))
        if not started and not preview:
            return LearningRecord(target_role=profile['target_role'],career_goal=profile['career_goal'],
                                  skills=[],next_topic=None,activity=None,completed_topics=0,total_topics=0,
                                  note='Create your learning roadmap when you are ready.').model_dump()
        if not saved or (saved["goal"]!=goal and not saved.get("evaluation_id")):
            saved={"goal":goal,"focus_skills":[r["skill"] for r in market[:6]]}
            if not preview:self.repo.write([item(pk,"CAREER_PATH#active",saved)])
        elif not saved.get('evaluation_id'):
            # Preserve paths the user opened while letting new demand refresh
            # the remaining focus slots. Evidence/history always stays intact.
            started=[s for s in saved["focus_skills"] if self.repo.get(pk,f"PATH#{s}")]
            focus=list(dict.fromkeys(started+[r["skill"] for r in market]))[:6]
            if focus!=saved["focus_skills"]:
                saved={**saved,"focus_skills":focus}
                if not preview:self.repo.write([item(pk,"CAREER_PATH#active",saved)])
        frequencies={r["skill"]:r["job_count"] for r in market}
        evidence={e["skill"]:e for e in self.service.skills(uid)}
        skills=[]
        next_topic=None
        for skill in saved["focus_skills"]:
            path=self.repo.get(pk,f"PATH#{skill}")
            if saved.get('evaluation_id') and (path or {}).get('evaluation_id')!=saved['evaluation_id']:path=None
            topics=[]
            for c in (path or {}).get("competencies",[]):
                result=self.repo.get(pk,f"COMPETENCY#{c['id']}")
                practiced=bool(self.repo.get(pk,f"PRACTICE#{c['id']}"))
                status="completed" if result and result["passed"] else "practice_needed" if result else "available"
                topic={**c,"status":status,"lesson_completed":practiced,"evidence":result}
                if next_topic is None and status!="completed":
                    topic["status"]="current" if not result else "practice_needed"
                    next_topic=topic
                topics.append(topic)
            skills.append({"skill":skill,"label":skill_label(skill),"job_count":frequencies.get(skill,0),
                           "rationale":path["rationale"] if path else "Explore focused competencies connected to this career goal.",
                           "expanded":path is not None,"topics":topics,
                           "mastery":"foundational" if evidence.get(skill,{}).get("passed") else "not_assessed"})
        return LearningRecord(evaluation_id=saved.get("evaluation_id"),summary=saved.get("summary"),target_role=saved["goal"]["target_role"],career_goal=saved["goal"]["career_goal"],skills=skills,next_topic=next_topic,
                              activity=(self.repo.get(pk,"ACTIVITY#active") or None),completed_topics=sum(t["status"]=="completed" for s in skills for t in s["topics"]),
                              total_topics=sum(len(s["topics"]) for s in skills),
                              note="Knowledge and scenario checks support foundational evidence. Applied and demonstrated levels require practical evidence and are not awarded by quizzes.").model_dump()

    def expand(self,uid,skill):
        skill=normalize_skills([skill])[0]
        plan=self.plan(uid,preview=True)
        if skill not in {s["skill"] for s in plan["skills"]}:
            raise ValueError("Choose a skill in your career roadmap")
        pk,sk=f"USER#{uid}",f"PATH#{skill}"
        saved=self.repo.get(pk,'CAREER_PATH#active') or {}
        existing=self.repo.get(pk,sk)
        if not existing or existing.get('evaluation_id')!=saved.get('evaluation_id'):
            generated=self.service.intelligence.skill_path(self.service.profile(uid),skill,self.service.market(uid)["requirements"][:8])
            data={"skill":skill,"evaluation_id":saved.get("evaluation_id"),"revision":0,"rationale":generated.rationale,"competencies":[
                {**c.model_dump(),"id":f"{skill}:{saved['evaluation_id']}-{i+1}" if saved.get("evaluation_id") else f"{skill}:{i+1}","skill":skill} for i,c in enumerate(generated.competencies)]}
            try:
                self.repo.write([item(pk,sk,data),item(pk,'CAREER_PATH#active',{
                    **saved,'requested':True,'goal':{k:self.service.profile(uid)[k] for k in ['current_role','target_role','career_goal']},
                    'focus_skills':[s['skill'] for s in plan['skills']]})],**({} if existing else {"absent":(pk,sk)}))
            except Conflict:
                pass
        return self.plan(uid)

    def start(self,uid):
        plan=self.plan(uid)
        if plan['skills']:
            return plan
        preview=self.plan(uid,preview=True)
        if not preview['skills']:
            raise ValueError('No role requirements are available to create a roadmap yet.')
        return self.expand(uid,preview['skills'][0]['skill'])

    def competency(self,uid,cid):
        skill=normalize_skills([cid.rsplit(":",1)[0]])[0]
        path=self.repo.get(f"USER#{uid}",f"PATH#{skill}") or {}
        for topic in path.get("competencies",[]):
            if topic["id"]==cid:
                return topic
        raise ValueError("Competency not found in your learning path")

    def lesson(self,uid,cid):
        topic=self.competency(uid,cid)
        pk,sk=f"USER#{uid}",f"COMPETENCY_CONTENT#{cid}"
        cached=self.repo.get(pk,sk)
        if not cached:
            evidence=self.repo.get(pk,f"COMPETENCY#{cid}")
            generated=self.service.intelligence.lesson(self.service.profile(uid),topic["skill"],[evidence] if evidence else [],topic)
            cached=generated.model_dump()
            self.repo.write([item(pk,sk,cached)])
        self.activity(uid,{"kind":"lesson","competency_id":cid,"skill":topic["skill"],"title":topic["title"]})
        return {**cached,"skill":topic["skill"],"competency_id":cid,"completed":bool(self.repo.get(pk,f"PRACTICE#{cid}"))}

    def practice(self,uid,cid):
        topic=self.competency(uid,cid)
        if not self.repo.get(f"USER#{uid}",f"COMPETENCY_CONTENT#{cid}"):
            raise ValueError("Open the lesson before recording practice")
        self.repo.write([item(f"USER#{uid}",f"PRACTICE#{cid}",{"completed":True})])
        return self.service.create_assessment(uid,topic["skill"],competency_id=cid)

    def activity(self,uid,data):
        self.repo.write([item(f"USER#{uid}","ACTIVITY#active",data)])

    def next_assessment(self,uid):
        plan=self.start(uid)
        topic=plan["next_topic"]
        if topic:
            return self.service.create_assessment(uid,topic["skill"],competency_id=topic["id"])
        missing=next((s for s in plan["skills"] if s["mastery"]=="not_assessed"),None)
        if missing:
            expanded=self.expand(uid,missing["skill"])
            topic=next(s for s in expanded["skills"] if s["skill"]==missing["skill"])["topics"][0]
            return self.service.create_assessment(uid,topic["skill"],competency_id=topic["id"])
        return self.service.create_assessment(uid,plan["skills"][0]["skill"] if plan["skills"] else "python")

    def passport(self,uid):
        skills=[SkillEvidence.model_validate({**e,"mastery":"foundational" if e["passed"] else "not_assessed"}).model_dump() for e in self.service.skills(uid)]
        topics=self.repo.partition(f"USER#{uid}","COMPETENCY#")
        return PassportRecord(skills=skills,competencies=topics,assessments=self.repo.partition(f"USER#{uid}","ASSESSMENT#"),
                              strengths=[e["title"] for e in topics if e["passed"]],next_steps=[e["title"] for e in topics if not e["passed"]],
                              note="Self-reported skills never change this passport. Foundational evidence comes from server-graded knowledge checks; higher mastery levels need practical work.").model_dump()
