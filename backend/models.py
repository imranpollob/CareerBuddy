from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StrictInt, SecretStr, EmailStr, field_validator, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(Contract):
    email: EmailStr = Field(max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)


class SignupRequest(LoginRequest):
    password: SecretStr = Field(min_length=12, max_length=128)
    name: str = Field(min_length=1, max_length=80)
    role: Literal["candidate", "employer"] = "candidate"
    current_role: str = Field(default="Getting started", min_length=1, max_length=120)
    target_role: str = Field(default="AI Engineer", min_length=1, max_length=120)
    candidate_track: Literal["career_switcher", "student", "experienced"] = "career_switcher"
    claimed_skills: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("claimed_skills")
    @classmethod
    def valid_claims(cls, values):
        from backend.tools.jobs import normalize_skills
        return normalize_skills(values)


class ProfileUpdate(Contract):
    name: str = Field(min_length=1, max_length=80)
    current_role: str = Field(min_length=1, max_length=120)
    target_role: str = Field(min_length=1, max_length=120)
    claimed_skills: list[str] = Field(max_length=20)
    marketplace_opt_in: bool = False
    career_goal: Literal["stay_relevant", "find_job", "switch_careers"] = "switch_careers"

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
    onboarding_completed: bool = True


class AccountSession(Contract):
    profile: Profile
    email: EmailStr
    mode: Literal["mock", "bedrock"]


class JobCreate(Contract):
    title: str = Field(min_length=3, max_length=120)
    company: str = Field(min_length=2, max_length=100)
    location: str = Field(default="Remote", max_length=100)
    description: str = Field(min_length=20, max_length=12000)
    required_skills: list[str] = Field(default_factory=list, max_length=20)
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
    skill_tags: list["SkillTag"] = Field(default_factory=list, max_length=20)
    tagging_method: Literal["keywords", "llm", "mock", "manual"] = "keywords"
    tagging_model: str | None = None
    tagged_at: str | None = None
    tagged_description_hash: str | None = None


class AssessmentCreate(Contract):
    skill: str = Field(default="python", max_length=50)
    competency_id: str | None = Field(default=None, max_length=80)


class Submission(Contract):
    answers: dict[str, StrictInt] = Field(min_length=1, max_length=5)


class ChatRequest(Contract):
    message: str = Field(min_length=1, max_length=3000)


class RuntimeRequest(ChatRequest):
    session_token: SecretStr = Field(min_length=32, max_length=128)


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
    mastery: Literal["not_assessed", "foundational", "applied", "demonstrated"] = "foundational"
    competency_ids: list[str] = Field(default_factory=list)
    assessment_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def mastery_requires_passing_evidence(self):
        if not self.passed:
            self.mastery="not_assessed"
        return self


class Question(Contract):
    id: str
    prompt: str
    choices: list[str]
    format: Literal["knowledge", "scenario"] = "knowledge"


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
    generation_model: str | None = None
    personalized_context: str | None = None
    competency_id: str | None = None
    competency_title: str | None = None
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
    examples: list[str] = Field(default_factory=list)
    key_takeaways: list[str] = Field(default_factory=list)
    competency_id: str | None = None


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


class SkillTag(Contract):
    skill: str = Field(min_length=2, max_length=64)
    label: str = Field(min_length=2, max_length=80)
    requirement: Literal["required", "preferred"]
    evidence_excerpt: str = Field(min_length=3, max_length=240)

    @field_validator("skill")
    @classmethod
    def normalize(cls, value):
        from backend.tools.jobs import normalize_skills
        return normalize_skills([value])[0]


class SkillClaim(Contract):
    skill: str = Field(min_length=2, max_length=64)
    label: str = Field(min_length=2, max_length=80)
    evidence_excerpt: str = Field(min_length=3, max_length=240)

    @field_validator("skill")
    @classmethod
    def normalize(cls, value):
        from backend.tools.jobs import normalize_skills
        return normalize_skills([value])[0]


class OnboardingTurn(Contract):
    question: str = Field(min_length=10, max_length=600)
    current_role: str = Field(min_length=1, max_length=120)
    target_role: str = Field(min_length=1, max_length=120)
    candidate_track: Literal["career_switcher", "student", "experienced"]
    claims: list[SkillClaim] = Field(default_factory=list, max_length=20)
    ready_to_review: bool
    career_goal: Literal["stay_relevant", "find_job", "switch_careers"] = "switch_careers"


class OnboardingAnswer(Contract):
    answer: str = Field(min_length=1, max_length=3000)
    revision: int = Field(ge=0)


class OnboardingConfirm(Contract):
    revision: int = Field(ge=0)


class OnboardingState(Contract):
    revision: int
    status: Literal["interview", "review", "completed"]
    mode: Literal["mock", "bedrock"]
    question: str
    messages: list[dict[str, str]]
    claims: list[SkillClaim]
    current_role: str
    target_role: str
    candidate_track: str
    career_goal: Literal["stay_relevant", "find_job", "switch_careers"] = "switch_careers"


class GeneratedQuestion(Question):
    id: str = Field(pattern=r"^q[1-4]$")
    prompt: str = Field(min_length=15,max_length=1400)
    correct_index: StrictInt = Field(ge=0, le=3)
    explanation: str = Field(min_length=10, max_length=1000)
    choices: list[str] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def unique_choices(self):
        if len(set(c.strip().lower() for c in self.choices)) != 4:
            raise ValueError("Assessment choices must be distinct")
        return self


class GeneratedAssessment(Contract):
    skill: str
    context_summary: str = Field(min_length=10, max_length=500)
    questions: list[GeneratedQuestion] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def unique_questions(self):
        if len({q.prompt.strip().lower() for q in self.questions}) != 4:
            raise ValueError("Assessment questions must be distinct")
        if len({q.id for q in self.questions}) != 4:
            raise ValueError("Assessment question IDs must be unique")
        return self


class TaggedPosting(Contract):
    job_id: str
    tags: list[SkillTag] = Field(min_length=1, max_length=15)


class TaggedPostings(Contract):
    postings: list[TaggedPosting] = Field(min_length=1, max_length=5)


class GeneratedLesson(Contract):
    title: str = Field(min_length=5, max_length=120)
    content: str = Field(min_length=50, max_length=5000)
    exercise: str = Field(min_length=20, max_length=1500)
    examples: list[str] = Field(min_length=1, max_length=3, description="One to three worked examples, each a string")
    key_takeaways: list[str] = Field(min_length=1, max_length=5, description="One to five concise takeaways, each a string; never null")


class CompetencyDefinition(Contract):
    title: str = Field(min_length=5, max_length=100)
    objective: str = Field(min_length=15, max_length=400)
    format: Literal["knowledge", "scenario"]


class GeneratedSkillPath(Contract):
    skill: str
    rationale: str = Field(min_length=15, max_length=500)
    competencies: list[CompetencyDefinition] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def distinct_topics(self):
        if len({c.title.casefold() for c in self.competencies}) != 3:
            raise ValueError("Competency titles must be distinct")
        return self


class ConversationMessage(Contract):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=12000)
    created_at: str
    specialists: list[str] = Field(default_factory=list)


class ConversationRecord(Contract):
    revision: int = 0
    messages: list[ConversationMessage] = Field(default_factory=list, max_length=24)


class LearningTopic(CompetencyDefinition):
    id: str
    skill: str
    status: Literal["available", "current", "completed", "practice_needed"]
    lesson_completed: bool
    evidence: dict | None = None


class LearningSkill(Contract):
    skill: str
    label: str
    job_count: int
    rationale: str
    expanded: bool
    topics: list[LearningTopic]
    mastery: Literal["not_assessed", "foundational", "applied", "demonstrated"]


class LearningRecord(Contract):
    target_role: str
    career_goal: str
    skills: list[LearningSkill]
    next_topic: LearningTopic | None
    activity: dict | None
    completed_topics: int
    total_topics: int
    note: str


class PassportRecord(Contract):
    skills: list[SkillEvidence]
    competencies: list[dict]
    assessments: list[AssessmentRecord]
    strengths: list[str]
    next_steps: list[str]
    note: str
