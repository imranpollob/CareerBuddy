from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json

from backend.db import Repository, item
from backend.models import Profile, ProfileUpdate, Job, JobCreate
from backend.tools.assessments import BANK, LESSONS, public_questions, grade
from backend.tools.jobs import SKILLS, requirements, normalize_skills, skill_label
from backend.tools.matching import match
from backend.demo import JOURNEYS


def now():
    return datetime.now(timezone.utc).isoformat()


class Service:
    def __init__(self, repo: Repository, settings=None):
        self.repo = repo
        self.include_samples = bool(settings and settings.seed_accounts)
        self.sample_user_ids={f["profile"]["id"] for f in json.loads((Path(__file__).parent/"data"/"demo_profiles.json").read_text())}
        self.intelligence = None
        if settings is not None:
            from backend.intelligence import Intelligence
            self.intelligence = Intelligence(settings)
        from backend.learning import Learning
        self.learning=Learning(self)

    def catalog(self, uid=None):
        result=dict(SKILLS)
        for job in self.jobs():
            for tag in job.get("skill_tags",[]):
                result.setdefault(tag["skill"],tag["label"])
        if uid:
            interview=self.repo.get(f"USER#{uid}","LEARNING_EVALUATION#active") or self.repo.get(f"USER#{uid}","ONBOARDING#active") or {}
            for claim in interview.get("claims",[]):
                result.setdefault(claim["skill"],claim["label"])
        return result

    def profile(self, uid="candidate-demo"):
        profile = self.repo.get(f"USER#{uid}", "PROFILE")
        if profile is None:
            raise ValueError("Profile not found")
        return Profile.model_validate(profile).model_dump()

    def update_profile(self, uid, update: ProfileUpdate):
        profile = Profile.model_validate({**self.profile(uid), **update.model_dump()}).model_dump()
        self.repo.write([item(f"USER#{uid}", "PROFILE", profile)])
        return profile

    def skills(self, uid):
        return self.repo.partition(f"USER#{uid}", "SKILL#")

    def jobs(self):
        active_ids = {j["id"] for j in json.loads((Path(__file__).parent / "data" / "jobs.json").read_text())
                      if self.include_samples or not j["synthetic"]}
        # Removed public snapshots stay stored for history but leave the active sample.
        return [j for j in self.repo.scan("DETAILS") if (j["id"] in active_ids or j.get("employer_id"))
                and (self.include_samples or not j.get("synthetic",False))]

    def market(self, uid=None):
        jobs = self.jobs()
        if uid and self.profile(uid)["candidate_track"] == "student":
            early = [j for j in jobs if j.get("career_level") in {"internship", "entry"}]
            if early:
                jobs = early
        return {"jobs": jobs, "requirements": requirements(jobs), "posting_count": len(jobs),
                "note": "Frequency is counted from this small posting sample; it is not a market-wide estimate."}

    def journey(self, uid):
        track = self.profile(uid)["candidate_track"]
        return JOURNEYS.get(track, JOURNEYS["career_switcher"])

    def create_job(self, employer_id, request: JobCreate):
        job = Job(**request.model_dump(), id=uuid4().hex, employer_id=employer_id,
                  source_name="Employer posting", retrieved_at=now(), synthetic=self.profile(employer_id)["synthetic"])
        data = job.model_dump(mode="json")
        if self.intelligence:
            if request.required_skills:
                data["description"] += "\nEmployer-declared required skills: " + ", ".join(skill_label(s) for s in request.required_skills)
            data=self.intelligence.tag_jobs([data])[0]
        if not data["required_skills"]:
            raise ValueError("No supported skill requirements were identified. Add more detail to the posting.")
        self.repo.write([item(f"JOB#{job.id}", "DETAILS", data)])
        return data

    def assessment(self, uid, aid):
        value = self.repo.get(f"USER#{uid}", f"ASSESSMENT#{aid}")
        if value is None:
            raise ValueError("Assessment not found")
        return value

    def create_assessment(self, uid, skill, *, fixed=False, competency_id=None):
        skill=normalize_skills([skill])[0]
        competency=self.learning.competency(uid,competency_id) if competency_id else None
        if competency and competency["skill"]!=skill:
            raise ValueError("Assessment skill does not match the competency")
        # Reuse an unsubmitted attempt, including if an agent retries a tool call.
        for existing in self.repo.partition(f"USER#{uid}", "ASSESSMENT#"):
            if existing["skill"] == skill and existing.get("competency_id")==competency_id and existing["status"] == "pending" and existing.get("evaluation_id")== (self.repo.get(f"USER#{uid}","CAREER_PATH#active") or {}).get("evaluation_id"):
                return existing
        aid=uuid4().hex
        data={"id":aid,"skill":skill,"status":"pending","created_at":now(),"evaluation_id":(self.repo.get(f"USER#{uid}","CAREER_PATH#active") or {}).get("evaluation_id")}
        writes=[]
        if self.intelligence and not fixed:
            interview=self.repo.get(f"USER#{uid}","LEARNING_EVALUATION#active") or self.repo.get(f"USER#{uid}","ONBOARDING#active") or {}
            prior=[q["prompt"] for a in self.repo.partition(f"USER#{uid}","ASSESSMENT#") if a["skill"]==skill for q in a["questions"]][-12:]
            context={"claimed_skill_evidence":interview.get("claims",[]),"prior_question_prompts":prior,
                     "latest_assessed_skills":self.skills(uid),"market_requirements":self.market(uid)["requirements"][:5]}
            if competency:
                context["target_competency"]=competency
                data.update(competency_id=competency_id,competency_title=competency["title"])
            generated=self.intelligence.assessment(self.profile(uid),skill,context)
            data.update(questions=[q.model_dump(exclude={"correct_index","explanation"}) for q in generated.questions],
                        kind="llm_generated_v1" if self.intelligence.settings.ai_mode=="bedrock" else "mock_generated_v1",
                        generation_model=self.intelligence.settings.model_id if self.intelligence.settings.ai_mode=="bedrock" else "offline fixture",
                        personalized_context=generated.context_summary)
            key={"questions":[{"id":q.id,"correct_index":q.correct_index,"explanation":q.explanation} for q in generated.questions]}
            writes.append(item(f"USER#{uid}",f"ASSESSMENT_KEY#{aid}",key))
        else:
            if skill not in BANK:
                raise ValueError("An AI model is required to create this assessment topic")
            data.update(questions=public_questions(skill),kind="fixed_fundamentals_v1")
        writes.append(item(f"USER#{uid}",f"ASSESSMENT#{aid}",data))
        self.repo.write(writes)
        if not fixed:
            self.learning.activity(uid,{"kind":"assessment","assessment_id":aid,"skill":skill,"competency_id":competency_id,"title":data.get("competency_title",skill_label(skill))})
        return data

    def submit(self, uid, aid, answers, *, seeded=False):
        data = self.assessment(uid, aid)
        if data["status"] != "pending":
            from backend.db import Conflict
            raise Conflict("Assessment has already been submitted")
        if data["kind"] in {"llm_generated_v1","mock_generated_v1"}:
            key=self.repo.get(f"USER#{uid}",f"ASSESSMENT_KEY#{aid}")
            if not key:
                raise ValueError("This assessment's answer key is unavailable")
            expected={q["id"] for q in key["questions"]}
            if set(answers)!=expected or any(type(v) is not int or v not in range(4) for v in answers.values()):
                raise ValueError("Submit one valid choice (0–3) for every question, with no extra questions")
            feedback=[{"question_id":q["id"],"correct":answers[q["id"]]==q["correct_index"],"explanation":q["explanation"]} for q in key["questions"]]
            score=100*sum(f["correct"] for f in feedback)//len(feedback)
            result={"score":score,"passed":score>=75,"feedback":feedback,"scope":f"Generated four-question {skill_label(data['skill'])} check; AI-authored questions are limited evidence, not certification"}
        else:
            result = grade(data["skill"], answers)
        data.update(status="completed", answers=answers, result=result, completed_at=now())
        if data.get("competency_id"):
            result["scope"]=f"Four-question competency knowledge check: {data['competency_title']}; limited foundational evidence, not certification"
        evidence = {"skill": data["skill"], "assessment_id": aid, "score": result["score"],
                    "passed": result["passed"], "assessed_at": data["completed_at"], "scope": result["scope"],
                    "synthetic": seeded}
        evidence["mastery"]="foundational" if result["passed"] else "not_assessed"
        pk, sk = f"USER#{uid}", f"ASSESSMENT#{aid}"
        writes=[item(pk,sk,data)]
        revision_guard=None
        if data.get("competency_id"):
            cid=data["competency_id"]
            topic={**evidence,"id":cid,"title":data["competency_title"],"assessment_format":"objective_knowledge_check"}
            writes.append(item(pk,f"COMPETENCY#{cid}",topic))
            path=self.repo.get(pk,f"PATH#{data['skill']}")
            if not path or cid not in {c['id'] for c in path['competencies']}:
                raise Conflict('This assessment belongs to an earlier roadmap. Start a check from your current learning path.')
            revision_guard=(pk,f"PATH#{data['skill']}",path["revision"])
            writes.append(item(pk,f"PATH#{data['skill']}",{**path,"revision":path["revision"]+1}))
            topic_evidence=[topic if c["id"]==cid else self.repo.get(pk,f"COMPETENCY#{c['id']}") for c in path["competencies"]]
            complete=all(e and e["passed"] for e in topic_evidence)
            previous=self.repo.get(pk,f"SKILL#{data['skill']}") or {}
            if complete or previous.get("competency_ids"):
                evidence.update(score=min((e["score"] if e else 0) for e in topic_evidence),passed=complete,
                                mastery="foundational" if complete else "not_assessed",
                                competency_ids=[c["id"] for c in path["competencies"]],
                                assessment_ids=[e["assessment_id"] for e in topic_evidence if e],
                                scope="Three competency knowledge checks; foundational evidence, not practical certification")
                writes.append(item(pk,f"SKILL#{data['skill']}",evidence))
        else:
            writes.append(item(pk,f"SKILL#{data['skill']}",evidence))
        self.repo.write(writes, pending=(pk, sk),expected_revision=revision_guard)
        return data

    def roadmap(self, uid):
        demonstrated = {s["skill"] for s in self.skills(uid) if s["passed"]}
        existing = self.repo.get(f"USER#{uid}", "ROADMAP#active") or {"id": "active", "milestones": []}
        previous = {m["skill"]: m for m in existing["milestones"]}
        milestones = []
        requirements = self.market(uid)["requirements"]
        if self.profile(uid)["candidate_track"] == "student":
            foundation_order = {"python": 0, "sql": 1, "llm": 2}
            requirements.sort(key=lambda r: (foundation_order.get(r["skill"], 3), -r["job_count"]))
        for requirement in requirements:
            skill = requirement["skill"]
            if skill in demonstrated and skill not in previous:
                continue
            completed_lesson = self.repo.get(f"USER#{uid}", f"LESSON#{skill}")
            milestones.append({"skill": skill, "title": LESSONS[skill][0] if skill in LESSONS else f"Build {skill_label(skill)} fundamentals", "job_count": requirement["job_count"],
                               "status": "completed" if skill in demonstrated else "needs_evidence",
                               "lesson_completed": bool(completed_lesson), "estimated_minutes": 20})
        roadmap = {"id": "active", "target_role": self.profile(uid)["target_role"], "milestones": milestones,
                   "updated_at": now(), "note": ("Start with Python and SQL foundations, then close gaps from the internship and entry-level sample." if self.profile(uid)["candidate_track"] == "student" else "Prioritized by observed job requirements and missing assessment evidence.")}
        self.repo.write([item(f"USER#{uid}", "ROADMAP#active", roadmap)])
        return roadmap

    def lesson(self, uid, skill):
        skill=normalize_skills([skill])[0]
        cached=self.repo.get(f"USER#{uid}",f"CONTENT#{skill}")
        if cached:
            title,content,exercise=cached["title"],cached["content"],cached["exercise"]
        elif self.intelligence:
            generated=self.intelligence.lesson(self.profile(uid),skill,[s for s in self.skills(uid) if s["skill"]==skill])
            title,content,exercise=generated.title,generated.content,generated.exercise
            cached=generated.model_dump()
            self.repo.write([item(f"USER#{uid}",f"CONTENT#{skill}",cached)])
        elif skill in LESSONS:
            title, content, exercise = LESSONS[skill]
        else:
            raise ValueError("An AI model is required for this lesson topic")
        return {"skill": skill, "title": title, "content": content, "exercise": exercise,
                "examples":(cached or {}).get("examples",[]),"key_takeaways":(cached or {}).get("key_takeaways",[]),
                "completed": bool(self.repo.get(f"USER#{uid}", f"LESSON#{skill}"))}

    def complete_lesson(self, uid, skill):
        self.lesson(uid, skill)
        self.repo.write([item(f"USER#{uid}", f"LESSON#{skill}", {"skill": skill, "completed_at": now()})])
        return self.create_assessment(uid, skill)

    def matches(self, uid):
        skills = self.skills(uid)
        matches = [match(job, skills) for job in self.jobs()]
        student = self.profile(uid)["candidate_track"] == "student"
        matches.sort(key=lambda m: (int(student and m["job"].get("career_level") not in {"entry", "internship"}),
                                    -m["supported_count"] / m["required_count"], m["job"]["title"]))
        # Store only compact match snapshots; never cache private candidate discovery.
        if matches:
            self.repo.write([item(f"USER#{uid}", f"MATCH#{m['job']['id']}",
                                 {"job_id": m["job"]["id"], "supported": m["supported"], "missing": m["missing"], "updated_at": now()})
                             for m in matches[:20]])
        return matches

    def candidates(self, employer_id, job_id):
        job = self.repo.get(f"JOB#{job_id}", "DETAILS")
        if job is None or job.get("employer_id") != employer_id:
            raise PermissionError("Only your own job postings can be used for candidate discovery")
        candidates = []
        for profile in self.repo.scan("PROFILE"):
            if not self.include_samples and profile["id"] in self.sample_user_ids:
                continue
            if profile["role"] != "candidate" or not profile["marketplace_opt_in"]:
                continue
            result = match(job, self.skills(profile["id"]))
            if not result["supported"]:
                continue
            # Deliberate projection: no contact info, answers, chat, or private roadmap.
            candidates.append({"id": profile["id"], "name": profile["name"], "current_role": profile["current_role"],
                               "target_role": profile["target_role"], "synthetic": profile["synthetic"],
                               "candidate_track": profile.get("candidate_track", "career_switcher"),
                               **{k: v for k, v in result.items() if k != "job"}})
        return sorted(candidates, key=lambda c: -c["supported_count"])

    def dashboard(self, uid):
        return {"profile": self.profile(uid), "skills": self.skills(uid), "roadmap": self.roadmap(uid),
                "assessments": sorted(self.repo.partition(f"USER#{uid}", "ASSESSMENT#"), key=lambda a: a["created_at"], reverse=True),
                "skill_catalog": self.catalog(uid), "market": self.market(uid), "journey": self.journey(uid)}

    def seed(self, *, include_samples=None):
        # Add missing fixtures without replacing edits, consent, or actual attempts.
        path = Path(__file__).parent / "data"
        if include_samples is not None:
            self.include_samples=include_samples
        for fixture in (json.loads((path / "demo_profiles.json").read_text()) if self.include_samples else []):
            profile = Profile.model_validate(fixture["profile"])
            pk = f"USER#{profile.id}"
            existing = self.repo.get(pk, "PROFILE")
            if not existing:
                self.repo.write([item(pk, "PROFILE", profile.model_dump())])
            elif "candidate_track" not in existing:
                self.repo.write([item(pk, "PROFILE", {**existing, "candidate_track": profile.candidate_track})])
            if existing and "career_goal" not in existing:
                self.repo.write([item(pk,"PROFILE",{**self.repo.get(pk,"PROFILE"),"career_goal":profile.career_goal})])
            for skill, target_score in fixture.get("seed_scores", {}).items():
                if self.repo.get(pk, f"SKILL#{skill}"):
                    continue
                attempt = self.create_assessment(profile.id, skill, fixed=True)
                answers = {f"q{i+1}": q[2] if i < target_score // 25 else (q[2] + 1) % 4 for i, q in enumerate(BANK[skill])}
                self.submit(profile.id, attempt["id"], answers, seeded=True)
        # Add new snapshot jobs, leaving employer-created and previously saved records intact.
        for raw in json.loads((path / "jobs.json").read_text()):
            if raw["synthetic"] and not self.include_samples:
                continue
            job = Job.model_validate(raw)
            existing = self.repo.get(f"JOB#{job.id}", "DETAILS")
            if not existing:
                self.repo.write([item(f"JOB#{job.id}", "DETAILS", job.model_dump(mode="json"))])
            elif not job.synthetic and job.tagging_method=="llm" and (existing.get("tagged_at")!=job.tagged_at or existing.get("source_name")!=job.source_name):
                self.repo.write([item(f"JOB#{job.id}","DETAILS",job.model_dump(mode="json"))])
            elif "career_level" not in existing:
                self.repo.write([item(f"JOB#{job.id}", "DETAILS", {**existing, "career_level": job.career_level})])
