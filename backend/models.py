from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StrictInt, field_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProfileUpdate(Contract):
    name: str = Field(min_length=1, max_length=80)
    current_role: str = Field(min_length=1, max_length=120)
    target_role: str = Field(min_length=1, max_length=120)
    claimed_skills: list[str] = Field(max_length=20)
    marketplace_opt_in: bool = False

    @field_validator("claimed_skills")
    @classmethod
    def valid_skills(cls, values):
        from backend.tools.jobs import normalize_skills
        return normalize_skills(values)


class Profile(ProfileUpdate):
    id: str
    role: Literal["candidate", "employer"]
    synthetic: bool = True
    candidate_track: Literal["career_switcher", "student", "experienced", "employer"] = "career_switcher"


class JobCreate(Contract):
    title: str = Field(min_length=3, max_length=120)
    company: str = Field(min_length=2, max_length=100)
    location: str = Field(default="Remote", max_length=100)
    description: str = Field(min_length=20, max_length=12000)
    required_skills: list[str] = Field(min_length=1, max_length=15)
    career_level: Literal["internship", "entry", "mid", "senior", "unspecified"] = "unspecified"

    @field_validator("required_skills")
    @classmethod
    def valid_skills(cls, values):
        from backend.tools.jobs import normalize_skills
        return normalize_skills(values)


class Job(JobCreate):
    id: str
    employer_id: str | None = None
    source_url: HttpUrl | None = None
    source_name: str
    retrieved_at: str
    synthetic: bool


class AssessmentCreate(Contract):
    skill: str = Field(default="python", max_length=50)


class Submission(Contract):
    answers: dict[str, StrictInt] = Field(min_length=1, max_length=5)


class ChatRequest(Contract):
    message: str = Field(min_length=1, max_length=3000)


class SpecialistResult(Contract):
    specialist: Literal["job_market", "assessment", "coach", "marketplace"]
    summary: str = Field(min_length=1, max_length=6000)
    # Authoritative data comes only from deterministic tools, never parsed LLM prose.
    data: dict


class Delegation(Contract):
    specialist: str
    tools: list[str]
    result: SpecialistResult


class ChatResponse(Contract):
    message: str
    mode: Literal["mock", "bedrock"]
    delegations: list[Delegation]


class SkillEvidence(Contract):
    skill: str
    assessment_id: str
    score: int = Field(ge=0, le=100)
    passed: bool
    assessed_at: str
    scope: str
    synthetic: bool


class Question(Contract):
    id: str
    prompt: str
    choices: list[str]


class Feedback(Contract):
    question_id: str
    correct: bool
    explanation: str


class AssessmentResult(Contract):
    score: int = Field(ge=0, le=100)
    passed: bool
    feedback: list[Feedback]
    scope: str


class AssessmentRecord(Contract):
    id: str
    skill: str
    status: Literal["pending", "completed"]
    created_at: str
    questions: list[Question]
    kind: str
    answers: dict[str, int] | None = None
    result: AssessmentResult | None = None
    completed_at: str | None = None


class Milestone(Contract):
    skill: str
    title: str
    job_count: int
    status: Literal["completed", "needs_evidence"]
    lesson_completed: bool
    estimated_minutes: int


class RoadmapRecord(Contract):
    id: str
    target_role: str
    milestones: list[Milestone]
    updated_at: str
    note: str


class LessonRecord(Contract):
    skill: str
    title: str
    content: str
    exercise: str
    completed: bool


class RequirementSource(Contract):
    job_id: str
    url: HttpUrl | None
    synthetic: bool
    retrieved_at: str


class SkillRequirement(Contract):
    skill: str
    label: str
    job_count: int
    sources: list[RequirementSource]


class MarketRecord(Contract):
    jobs: list[Job]
    requirements: list[SkillRequirement]
    posting_count: int
    note: str


class MatchRecord(Contract):
    job: Job
    supported: list[str]
    missing: list[str]
    supported_count: int
    required_count: int
    evidence: list[SkillEvidence]
    explanation: str


class CandidateMatch(Contract):
    id: str
    name: str
    current_role: str
    target_role: str
    synthetic: bool
    candidate_track: Literal["career_switcher", "student", "experienced", "employer"]
    supported: list[str]
    missing: list[str]
    supported_count: int
    required_count: int
    evidence: list[SkillEvidence]
    explanation: str


class DashboardRecord(Contract):
    profile: Profile
    skills: list[SkillEvidence]
    roadmap: RoadmapRecord
    assessments: list[AssessmentRecord]
    skill_catalog: dict[str, str]
    market: MarketRecord
    journey: "Journey"


class Journey(Contract):
    title: str
    description: str
    portfolio_project: str
    suggested_prompt: str
    target_levels: list[str]
