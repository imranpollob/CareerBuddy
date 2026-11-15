# SkillPilot data and API contracts

One table, `SkillPilot`, with string keys `PK` and `SK`. Every item has a `data` map. Records are limited to 350 KB in the application, below DynamoDB's item limit. No indexes are required for the small demo.

| Logical entity | PK | SK | Access pattern |
| --- | --- | --- | --- |
| User | `USER#<id>` | `PROFILE` | Get authenticated profile; scan profiles for consent-filtered employer discovery |
| UserSkill | `USER#<id>` | `SKILL#<skill>` | Query latest assessment-backed evidence for that user |
| Assessment | `USER#<id>` | `ASSESSMENT#<attempt-id>` | Get owned attempt; query attempt history |
| Roadmap | `USER#<id>` | `ROADMAP#active` | Get/replace compact derived learning plan |
| Lesson progress | `USER#<id>` | `LESSON#<skill>` | Record that the candidate practiced the lesson |
| Job | `JOB#<id>` | `DETAILS` | Get posting; scan compact job sample |
| Match | `USER#<id>` | `MATCH#<job-id>` | Store derived supported/missing skill snapshot |

`Profile.claimed_skills` is self-reported. It never contributes to assessed coverage. `SKILL#...` items contain the latest submitted assessment's score, pass status, attempt ID, date, and limited scope. A later failed assessment replaces the skill's current passing evidence; historical attempts remain intact.

Submission writes the completed assessment and skill evidence in one DynamoDB transaction, conditional on the attempt still being pending. The memory repository applies the same rule under a lock. A replay returns 409. A candidate cannot choose a user ID, role, score, pass status, or evidence ID in the submission contract.

Roadmaps compare AI-engineering job samples with demonstrated skills. Career switchers use the full active sample; students use internship/entry title labels and start with Python/SQL foundations. Journey and career-stage preferences are context, not evidence of eligibility. Changing the target-role text does not fetch a new career-specific dataset in this MVP. A milestone becomes complete when its fundamentals assessment passes. Lesson completion alone creates no evidence. Reassessment uses a fresh attempt of the fixed question bank, not an equivalent alternate exam.

Matching is set intersection: supported requirements = normalized job skills intersecting currently passed fundamentals evidence. Coverage is `supported_count / required_count`; there is no hiring score. For sourced jobs, skill mentions are extracted by documented keyword rules. Mentions may include optional skills or general company descriptions; users must review the original posting. The sample spans nine employers and is not a representative labor-market survey.

Employer discovery checks ownership of the selected posting and the candidate's current opt-in on every request. It returns only display name, current/target role, relevant evidence summaries, and skill gaps. Answers, private chat, claimed skills, and learning history are excluded. No discovery cache is persisted. The demo candidate profile is synthetic, but assessments taken through the UI are actually graded; only seeded evidence is synthetic.

The backend's Pydantic contracts are in `backend/models.py`; frontend response interfaces are in `frontend/src/api.ts`. `/docs` exposes FastAPI's OpenAPI UI. Routes derive identity from an HttpOnly demo session cookie. There are intentionally three public demo login endpoints bound to fixed identities: engineer (`candidate`), `student`, and `employer`. Both candidate identities have the candidate role; user IDs are server-controlled. This is a local demonstration, not production authentication.

| Route | Role | Purpose |
| --- | --- | --- |
| `POST /api/demo/candidate`, `POST /api/demo/student`, `POST /api/demo/employer` | Public | Start a fixed server-controlled demo session |
| `GET /api/dashboard`, `PATCH /api/profile` | Candidate | Own profile, skills, roadmap, assessment history; update only allowed profile fields |
| `POST /api/assessments`, `GET /api/assessments/{id}` | Candidate | Create/read own attempt, no pending answer key |
| `POST /api/assessments/{id}/submit` | Candidate | Validate answers, grade in Python, atomically store evidence |
| `GET /api/roadmap`, `GET /api/lessons/{skill}` | Candidate | Derived roadmap and working lesson |
| `POST /api/lessons/{skill}/complete` | Candidate | Mark lesson practiced and prepare reassessment |
| `GET /api/matches` | Candidate | Own evidence compared with job requirements |
| `POST /api/jobs`, `GET /api/employer/jobs` | Employer | Create a labeled demo posting; list own jobs |
| `GET /api/employer/jobs/{id}/candidates` | Employer | Discover consenting profiles for an owned job |
| `POST /api/chat` | Authenticated | Orchestrator response and actual specialist/tool delegation results |
| `GET /api/jobs`, `GET /api/market` | Authenticated | Sample postings and deterministic skill frequencies |

