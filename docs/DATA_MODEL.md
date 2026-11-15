# SkillPilot data and API contracts

One table, `SkillPilot`, with string keys `PK` and `SK`. Every item has a `data` map. Records are limited to 350 KB in the application, below DynamoDB's item limit. No indexes are required for the small demo.

| Logical entity | PK | SK | Access pattern |
| --- | --- | --- | --- |
| User | `USER#<id>` | `PROFILE` | Get authenticated profile; scan profiles for consent-filtered employer discovery |
| UserSkill | `USER#<id>` | `SKILL#<skill>` | Query latest assessment-backed evidence for that user |
| Assessment | `USER#<id>` | `ASSESSMENT#<attempt-id>` | Get owned attempt; query attempt history |
| Private answer key | `USER#<id>` | `ASSESSMENT_KEY#<attempt-id>` | Server-side grading only; excluded from API/history queries |
| Adaptive interview | `USER#<id>` | `ONBOARDING#active` | Resume private conversation, claims, and revision-guarded confirmation |
| Career path | `USER#<id>` | `CAREER_PATH#active` | Save career goal and six focus skills; preserve opened paths as market demand changes |
| Skill competencies | `USER#<id>` | `PATH#<skill>` | Three generated objectives and a revision used to guard concurrent grading |
| Competency evidence | `USER#<id>` | `COMPETENCY#<skill>:<number>` | Latest objective-check result for a narrow topic |
| Competency lesson | `USER#<id>` | `COMPETENCY_CONTENT#<id>` | Private structured explanation, examples, takeaways and practice |
| Competency practice | `USER#<id>` | `PRACTICE#<id>` | Practice marker, not assessed evidence |
| Last activity | `USER#<id>` | `ACTIVITY#active` | Resume a lesson or pending assessment |
| Conversation | `USER#<id>` | `CHAT#active` | Revision-guarded private text history, bounded to 24 messages |
| Generated lesson | `USER#<id>` | `CONTENT#<skill>` | Cache personalized lesson and exercise |
| Roadmap | `USER#<id>` | `ROADMAP#active` | Get/replace compact derived learning plan |
| Lesson progress | `USER#<id>` | `LESSON#<skill>` | Record that the candidate practiced the lesson |
| Job | `JOB#<id>` | `DETAILS` | Get posting; scan compact job sample |
| Match | `USER#<id>` | `MATCH#<job-id>` | Store derived supported/missing skill snapshot |

`Profile.claimed_skills` is self-reported. It never contributes to assessed coverage. `SKILL#...` items contain the latest submitted assessment's score, pass status, attempt ID, date, and limited scope. A later failed assessment replaces the skill's current passing evidence; historical attempts remain intact.

Submission writes the completed assessment and skill evidence in one DynamoDB transaction, conditional on the attempt still being pending. The memory repository applies the same rule under a lock. A replay returns 409. A candidate cannot choose a user ID, role, score, pass status, or evidence ID in the submission contract.

Roadmaps compare AI-engineering job samples with demonstrated skills. Career switchers use the full active sample; students use internship/entry title labels and start with Python/SQL foundations. Changing the target-role text does not fetch a new career-specific dataset. A milestone becomes complete when its assessment passes. Lesson completion alone creates no evidence. In Bedrock mode, reassessment generates fresh questions using prior prompts and personal context; offline mode uses labeled reference fixtures.

Matching is set intersection: supported requirements = normalized job skills intersecting currently passed assessment evidence. Coverage is `supported_count / required_count`; there is no hiring score. Bedrock tags job descriptions with normalized skill IDs, required/preferred status and exact source excerpts. If all identified skills are preferred, coverage uses that skill set; tags preserve the distinction. Users should review original postings. The sample spans nine employers and is not a market-wide survey.

Onboarding confirmation writes the profile and completed interview atomically, conditional on the expected conversation revision. Only server-saved claims can be confirmed; clients cannot submit a replacement skill list through that endpoint. Interview excerpts must occur in the user's answers. They remain claims and never create `SKILL#` evidence. Private labels are scoped to that user's catalog.

Employer discovery checks ownership of the selected posting and the candidate's current opt-in on every request. It returns only display name, current/target role, relevant evidence summaries, and skill gaps. Answers, private chat, claimed skills, and learning history are excluded. No discovery cache is persisted. The demo candidate profile is synthetic, but assessments taken through the UI are actually graded; only seeded evidence is synthetic.

The backend's Pydantic contracts are in `backend/models.py`; frontend response interfaces are in `frontend/src/api.ts`. `/docs` exposes FastAPI's OpenAPI UI. Routes derive identity from an expiring, HttpOnly account session cookie. Email/password signup and login support new users; three regular actor accounts are precreated. Passwords are hashed with Argon2, session tokens are stored only as digests, and logout revokes the session. See [authentication](AUTHENTICATION.md) for the additional account/session records in this same table.

| Route | Role | Purpose |
| --- | --- | --- |
| `POST /api/auth/signup`, `POST /api/auth/login` | Public | Create an account or verify credentials; establish an expiring session |
| `POST /api/auth/logout`, `GET /api/session` | Account | Revoke or inspect the current account session |
| `GET /api/dashboard`, `PATCH /api/profile` | Candidate | Own profile, skills, roadmap, assessment history; update only allowed profile fields |
| `GET /api/onboarding` | Candidate | Start or resume the private adaptive interview |
| `POST /api/onboarding/answer`, `POST /api/onboarding/complete` | Candidate | Answer the current revision; confirm server-saved claims |
| `POST /api/assessments`, `GET /api/assessments/{id}` | Candidate | Create/read own attempt, no pending answer key |
| `POST /api/assessments/{id}/submit` | Candidate | Validate answers, grade in Python, atomically store evidence |
| `GET /api/roadmap`, `GET /api/lessons/{skill}` | Candidate | Derived roadmap and working lesson |
| `POST /api/lessons/{skill}/complete` | Candidate | Mark lesson practiced and prepare reassessment |
| `GET /api/matches` | Candidate | Own evidence compared with job requirements |
| `POST /api/jobs`, `GET /api/employer/jobs` | Employer | Create a posting; list own jobs |
| `GET /api/employer/jobs/{id}/candidates` | Employer | Discover consenting profiles for an owned job |
| `POST /api/chat` | Authenticated | Orchestrator response and actual specialist/tool delegation results |
| `GET /api/jobs`, `GET /api/market` | Authenticated | Sample postings and deterministic skill frequencies |


CareerBuddy adds `career_goal` (`stay_relevant`, `find_job`, `switch_careers`) to profiles. Skill evidence has server-derived mastery and optional supporting competency/assessment IDs. Passing a narrow topic writes only competency evidence. All three topic passes are needed to support the broader skill; a later failed competency invalidates that aggregate. Path revision and pending-attempt conditions guard these writes in one transaction. Standalone skill checks remain available. Quizzes award at most Foundational, never Applied or Demonstrated.

Additional owner-scoped candidate endpoints: `GET /api/learning`, `POST /api/learning/{skill}/expand`, `GET /api/competencies/{id}/lesson`, `POST /api/competencies/{id}/practice`, `POST /api/assessments/next`, and `GET /api/passport`. `POST /api/assessments` accepts an optional owned `competency_id`; mismatched skill/topic pairs are rejected. `GET /api/chat/history` is available to both roles and returns only their own conversation text and specialist names.
