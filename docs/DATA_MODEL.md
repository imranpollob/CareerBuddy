# Data model and API reference

Current implementation: [backend/models.py](../backend/models.py), [backend/db.py](../backend/db.py), [backend/api.py](../backend/api.py), and [typed frontend contracts](../frontend/src/api.ts). The [README](../README.md) describes product behavior and architecture. Interactive OpenAPI documentation is available at http://127.0.0.1:8000/docs while the backend runs.

## Single-table keys

One table, `SkillPilot`, uses string `PK` and `SK` keys and a `data` map per item. The application limits records to 350 KB. No secondary indexes are required for this small dataset; job/profile scans are bounded MVP access patterns.

| Record | PK | SK | Access pattern |
| --- | --- | --- | --- |
| Account | `ACCOUNT#<normalized-email-hash>` | `CREDENTIALS` | Lookup by normalized email; stores user ID, email, Argon2 hash |
| Session | `SESSION#<token-hash>` | `AUTH_SESSION` | Resolve identity and expiry; logout revokes the session |
| Profile | `USER#<id>` | `PROFILE` | Own profile, explicit goal confirmation, and neutral unknown fields; consent-filtered employer discovery scans |
| Current skill evidence | `USER#<id>` | `SKILL#<skill>` | Query the user's latest assessment-backed evidence |
| Assessment attempt | `USER#<id>` | `ASSESSMENT#<attempt-id>` | Owned attempt and history, including evaluation/topic references |
| Private answer key | `USER#<id>` | `ASSESSMENT_KEY#<attempt-id>` | Server-side grading only; excluded from public responses |
| Background onboarding | `USER#<id>` | `ONBOARDING#active` | Four numbered answers, progress, and confirmation revision |
| Learning evaluation | `USER#<id>` | `LEARNING_EVALUATION#active` | Three-question adaptive interview, grounded claims, goal, state, revision, evaluation ID |
| Active career path | `USER#<id>` | `CAREER_PATH#active` | Ordered focus skills, summary, goal, and confirmed evaluation ID |
| Generated skill path | `USER#<id>` | `PATH#<skill>` | Three competencies, evaluation ID, and grading revision |
| Archived skill path | `USER#<id>` | `PATH_HISTORY#<evaluation-id-or-legacy>#<skill>` | Retain previous generated path content during replacement |
| Competency evidence | `USER#<id>` | `COMPETENCY#<topic-id>` | Latest narrow-topic assessment result |
| Competency lesson | `USER#<id>` | `COMPETENCY_CONTENT#<topic-id>` | Private explanation, examples, takeaways, practice |
| Practice marker | `USER#<id>` | `PRACTICE#<topic-id>` | Record practice; does not establish skill evidence |
| Last activity | `USER#<id>` | `ACTIVITY#active` | Resume a current lesson or assessment |
| Chat history | `USER#<id>` | `CHAT#active` | Revision-guarded private history, latest 24 text messages |
| Job | `JOB#<id>` | `DETAILS` | Public snapshot or employer-owned posting, sources and skill tags |
| Match snapshot | `USER#<id>` | `MATCH#<job-id>` | Derived supported/missing requirements; no candidate-discovery cache |
| Earlier broad-skill roadmap | `USER#<id>` | `ROADMAP#active` | Compact derived milestones used by retained service/API operations |
| Broad-skill lesson | `USER#<id>` | `CONTENT#<skill>` | Retained standalone lesson cache |
| Broad-skill practice | `USER#<id>` | `LESSON#<skill>` | Retained standalone practice/reassessment flow |

New topic IDs have the form `<skill>:<evaluation-id>-<1..3>`; earlier paths may use `<skill>:<1..3>`. Versioned IDs separate replacement-roadmap activity from prior attempts. Archived paths are stored data; there is no dedicated archive-browsing UI.

## Identity, privacy, and transactions

- Signup atomically inserts a UUID profile and credential record, conditional on the email key being absent. Normal startup creates no fixture accounts.
- Authentication uses a random HttpOnly, SameSite=Strict cookie. Only the token digest is stored. Sessions default to four hours, rotate on login, and are revoked on logout. Expiry is enforced in application code; AWS TTL infrastructure is not provisioned.
- Endpoints derive IDs and roles from the session. Profile edits cannot modify roles, scores, or assessment evidence. Login/signup attempt limits and origin checks are applied in FastAPI/auth code.
- Onboarding confirmation atomically saves background and completed state with a revision guard. It creates neither an assessment nor a personal roadmap.
- Learning evaluation checks skill excerpts against user answers. Confirmation validates and normalizes model-selected focus IDs, uses requirements from matching job titles when available, and generates the first path before committing the profile, completed evaluation, active roadmap, path, and archives under the expected interview revision.
- Re-evaluation leaves the old roadmap available until confirmation succeeds. Earlier attempts and evidence are retained; active progress uses the current version's topics. Changing profile goal text alone does not replace an evaluated roadmap.
- Assessment generation stores public questions and private keys together. Submission accepts choices only; Python computes the result. Completed attempt/evidence writes require a pending attempt, and competency aggregation also checks the path revision. Replay or stale writes return 409.
- Employer discovery checks posting ownership and current candidate opt-in every time. It returns relevant evidence and match explanations, excluding private answers, chat, and learning history.

## Evidence and matching

Self-reported background and `claimed_skills` provide generation context; they never count as assessed coverage. Standalone objective skill checks can establish limited Foundational evidence. For a competency path, all three topic passes are required to support the broader skill. Later failed assessments can invalidate current evidence while preserving attempt history. Applied/Demonstrated mastery is not awarded by quizzes.

Matching intersects normalized job requirements with currently passed skill evidence. Coverage is `supported_count / required_count`, not a hiring score. Required/preferred tags retain exact source excerpts; if a posting has only preferred tags, coverage uses that tracked skill set. Career-stage labels do not establish eligibility. The saved public dataset focuses on AI engineering and related roles.

## Endpoint groups

All paths below are relative to `/api`. Typed request/response schemas in OpenAPI are authoritative.

| Endpoint | Access | Purpose |
| --- | --- | --- |
| `GET /health` | Public | Mode, model configuration, repository health response |
| `POST /auth/signup`, `POST /auth/login` | Public | Register/authenticate and establish a cookie session |
| `POST /auth/logout` | Cookie, if present | Revoke session and clear cookie |
| `GET /session` | Account | Own profile, email, and AI mode |
| `GET /dashboard`, `PATCH /profile` | Candidate | Own summary and allowed profile edits |
| `GET /onboarding` | Candidate | Initialize/resume the four-question background flow |
| `POST /onboarding/answer`, `POST /onboarding/complete` | Candidate | Validate answers/revision; confirm background |
| `GET /learning` | Candidate | Read active plan; fresh users receive an empty plan |
| `GET /learning/evaluation` | Candidate | Read current evaluation or null |
| `POST /learning/evaluation` | Candidate | Start/resume an interview; begin a new one after completion |
| `POST /learning/evaluation/answer` | Candidate | Generate a follow-up or review after the third answer |
| `POST /learning/evaluation/complete` | Candidate | Confirm the reviewed profile and generate/replace the roadmap |
| `POST /learning` | Candidate | Return an existing evaluated plan; evaluation required |
| `POST /learning/{skill}/expand` | Candidate | Generate missing competencies in an evaluated roadmap |
| `GET /competencies/{id}/lesson` | Candidate | Generate/read an owned competency lesson |
| `POST /competencies/{id}/practice` | Candidate | Record practice and prepare an assessment |
| `POST /assessments`, `GET /assessments/{id}` | Candidate | Explicitly create/read an owned attempt; no pending answer key |
| `POST /assessments/next` | Candidate | Prepare the next evaluated-roadmap competency check |
| `POST /assessments/{id}/submit` | Candidate | Deterministic grading and atomic evidence writes |
| `GET /passport` | Candidate | Own skill/competency evidence and attempt history |
| `GET /matches` | Candidate | Compare own evidence with shared postings |
| `GET /roadmap`, `GET /lessons/{skill}`, `POST /lessons/{skill}/complete` | Candidate | Retained broad-skill roadmap/lesson operations |
| `GET /jobs`, `GET /market` | Account | Shared active postings and counted requirements |
| `POST /jobs`, `GET /employer/jobs` | Employer | Analyze/create a posting; list owned postings |
| `GET /employer/jobs/{id}/candidates` | Employer | Discover consenting candidates for an owned posting |
| `POST /chat`, `GET /chat/history` | Account | Orchestrator conversation/delegation and private text history |

`GET /learning` does not create a roadmap for a fresh user. Some other reads derive/cache records or generate lesson content on explicit opening; this API is a local MVP rather than a uniformly read-only REST design.

`goal_confirmed` records explicit user intent. New users have empty role/target fields, unspecified career purpose/track, and no claimed skills. Background onboarding does not infer a career purpose from student status. Learning evaluation requires target role and career purpose on its first answer and keeps those user values authoritative over model suggestions. Legacy unconfirmed defaults are normalized in API/model context without deleting stored evidence.

Career paths store `market_role_covered` and `market_job_ids`. Exact normalized title-phrase matching conservatively selects the saved postings relevant to a target role. Roles outside the snapshot can use new validated skill IDs and general learning guidance; they do not inherit AI-job demand counts. Current-path lessons and assessments use only the selected market subset.
