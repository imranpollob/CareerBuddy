from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json

from backend.db import Repository, item
from backend.models import Profile, ProfileUpdate, Job, JobCreate
from backend.tools.assessments import BANK, LESSONS, public_questions, grade
from backend.tools.jobs import SKILLS, requirements
from backend.tools.matching import match
from backend.demo import JOURNEYS


def now():
    return datetime.now(timezone.utc).isoformat()


class Service:
    def __init__(self, repo: Repository):
        self.repo = repo

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
        active_ids = {j["id"] for j in json.loads((Path(__file__).parent / "data" / "jobs.json").read_text())}
        # Removed public snapshots stay stored for history but leave the active sample.
        return [j for j in self.repo.scan("DETAILS") if j["id"] in active_ids or j.get("employer_id")]

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
        self.repo.write([item(f"JOB#{job.id}", "DETAILS", data)])
        return data

    def assessment(self, uid, aid):
        value = self.repo.get(f"USER#{uid}", f"ASSESSMENT#{aid}")
        if value is None:
            raise ValueError("Assessment not found")
        return value

    def create_assessment(self, uid, skill):
        if skill not in BANK:
            raise ValueError("Unsupported assessment topic")
        # Reuse an unsubmitted attempt, including if an agent retries a tool call.
        for existing in self.repo.partition(f"USER#{uid}", "ASSESSMENT#"):
            if existing["skill"] == skill and existing["status"] == "pending":
                return existing
        data = {"id": uuid4().hex, "skill": skill, "status": "pending", "created_at": now(),
                "questions": public_questions(skill), "kind": "fixed_fundamentals_v1"}
        self.repo.write([item(f"USER#{uid}", f"ASSESSMENT#{data['id']}", data)])
        return data

    def submit(self, uid, aid, answers, *, seeded=False):
        data = self.assessment(uid, aid)
        if data["status"] != "pending":
            from backend.db import Conflict
            raise Conflict("Assessment has already been submitted")
        result = grade(data["skill"], answers)
        data.update(status="completed", answers=answers, result=result, completed_at=now())
        evidence = {"skill": data["skill"], "assessment_id": aid, "score": result["score"],
                    "passed": result["passed"], "assessed_at": data["completed_at"], "scope": result["scope"],
                    "synthetic": seeded}
        pk, sk = f"USER#{uid}", f"ASSESSMENT#{aid}"
        self.repo.write([item(pk, sk, data), item(pk, f"SKILL#{data['skill']}", evidence)], pending=(pk, sk))
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
            milestones.append({"skill": skill, "title": LESSONS[skill][0], "job_count": requirement["job_count"],
                               "status": "completed" if skill in demonstrated else "needs_evidence",
                               "lesson_completed": bool(completed_lesson), "estimated_minutes": 20})
        roadmap = {"id": "active", "target_role": self.profile(uid)["target_role"], "milestones": milestones,
                   "updated_at": now(), "note": ("Start with Python and SQL foundations, then close gaps from the internship and entry-level sample." if self.profile(uid)["candidate_track"] == "student" else "Prioritized by observed job requirements and missing assessment evidence.")}
        self.repo.write([item(f"USER#{uid}", "ROADMAP#active", roadmap)])
        return roadmap

    def lesson(self, uid, skill):
        if skill not in LESSONS:
            raise ValueError("Lesson not found")
        title, content, exercise = LESSONS[skill]
        return {"skill": skill, "title": title, "content": content, "exercise": exercise,
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
                "skill_catalog": SKILLS, "market": self.market(uid), "journey": self.journey(uid)}

    def seed(self):
        # Add missing fixtures without replacing edits, consent, or actual attempts.
        path = Path(__file__).parent / "data"
        for fixture in json.loads((path / "demo_profiles.json").read_text()):
            profile = Profile.model_validate(fixture["profile"])
            pk = f"USER#{profile.id}"
            existing = self.repo.get(pk, "PROFILE")
            if not existing:
                self.repo.write([item(pk, "PROFILE", profile.model_dump())])
            elif "candidate_track" not in existing:
                self.repo.write([item(pk, "PROFILE", {**existing, "candidate_track": profile.candidate_track})])
            for skill, target_score in fixture.get("seed_scores", {}).items():
                if self.repo.get(pk, f"SKILL#{skill}"):
                    continue
                attempt = self.create_assessment(profile.id, skill)
                answers = {f"q{i+1}": q[2] if i < target_score // 25 else (q[2] + 1) % 4 for i, q in enumerate(BANK[skill])}
                self.submit(profile.id, attempt["id"], answers, seeded=True)
        # Add new snapshot jobs, leaving employer-created and previously saved records intact.
        for raw in json.loads((path / "jobs.json").read_text()):
            job = Job.model_validate(raw)
            existing = self.repo.get(f"JOB#{job.id}", "DETAILS")
            if not existing:
                self.repo.write([item(f"JOB#{job.id}", "DETAILS", job.model_dump(mode="json"))])
            elif "career_level" not in existing:
                self.repo.write([item(f"JOB#{job.id}", "DETAILS", {**existing, "career_level": job.career_level})])
