# MVP validation

Validated locally on November 14, 2026 (America/Detroit).

| Area | Status and evidence |
| --- | --- |
| Candidate onboarding | Implemented: separate software-engineer and student identities, editable career profiles, self-reported skills, goal and explicit discovery consent |
| Job intelligence | Implemented: 42 attributed public postings across nine employers (eight early-career), six labeled synthetic jobs, normalized keyword extraction and Python skill-frequency counts |
| Assessment | Implemented: seven topics, four fixed objective questions each, strict server-held keys, validated answers, pass threshold and feedback |
| Evidence persistence | Implemented: memory and single-table DynamoDB; actual DynamoDB Local tested for atomic submission, reload and replay rejection |
| Coaching | Implemented: evidence gaps, demand-prioritized milestones, seven short lessons/exercises, and fresh reassessment |
| Candidate matching | Implemented: explicit supported/missing skill lists and evidence counts, updated after reassessment |
| Employer marketplace | Implemented: create demo jobs, enforce job ownership, discover consenting profiles and inspect relevant evidence summaries |
| Multi-agent system | Implemented: one Strands orchestrator and four separate Strands specialist agents as tools; typed structured summaries and recorded delegation results |
| Live Bedrock | Passed: Nova 2 Lite invoked locally and completed four focused specialist delegation checks |
| Live integration | Passed: browser chat delegated through Bedrock to Assessment, persisted a new attempt in actual DynamoDB Local, and opened the assessment dialog; live Marketplace also read passing local database evidence |
| Offline AI | Implemented and labeled: deterministic Model fixture inside the actual Strands agent/tool loops |
| Frontend | Implemented: responsive candidate dashboard, job marketplace, employer dashboard, and orchestrator chat |
| Protection | Tested: reject profile evidence/identity mutations, reject invalid/replayed submissions, block wrong-role/foreign-record access, filter opt-out profiles, reject unrelated cross-origin writes |
| Backend tests | 36 passed with pytest, including memory and Moto-backed DynamoDB parity |
| Browser tests | Four full-flow tests passed, desktop 1440px and iPhone-size Chromium; no page errors or horizontal overflow |
| Frontend build | TypeScript check and Vite production build passed |
| AgentCore entrypoint | Local `/ping` and `/invocations` both returned 200 in mock mode; nothing deployed |
| Deployment image | Recipe and pinned requirements prepared; image build untested because Docker is not installed |

The browser scenario actually submits a failing Python attempt, opens the lesson, passes a fresh assessment, verifies increased requirement coverage, opts into discovery, inspects evidence as an employer, and creates another demo job. Screenshots and live-check reports are in ignored `.local/`. The final live browser check left a pending Python assessment for the candidate, ready to resume; it did not assign a score.

The live checks verify appropriate specialist names and authoritative tool data, not just plausible prose. Deterministic business tests establish correctness of scores, persistence, and matches. Model-generated explanations are helpful presentation, not the source of evidence. There is no paid LLM-as-judge evaluation in the default suite; the tests apply the workshop's output and trajectory evaluation principles using deterministic assertions.

Deliberate MVP limits:

- Two AI-engineering journeys with a shared sourced sample and student stage filtering; role-text edits do not select a new career dataset.
- Fixed small assessments and repeated question banks, not certification or fraud-resistant proctored exams.
- Keyword skill extraction may include optional mentions; public postings can close, and the bounded employer sample is not a market-wide survey.
- Three public fixed demo identities, local sessions and single-process execution; no production login or employer verification.
- Public-job refresh is manual; new snapshot IDs are seeded on restart; existing contents remain unchanged, and removed public IDs leave the active sample.
- AgentCore remote identity forwarding, IAM/table provisioning, image build, and AWS deployment remain unperformed.

Rerun the commands in README before the demo, particularly if temporary AWS credentials change. No AWS resources were created during validation.

The expanded demo additionally verifies student/engineer assessment isolation, a student foundations-first roadmap, early-career filtering, student opt-in discovery, non-synthetic provenance on actual student submissions, and safe additive seeding. See [the demo guide](DEMO_GUIDE.md).

The expanded student Coach and employer Marketplace paths also passed live Nova 2 Lite checks against the actual local DynamoDB table. Employer chat uses a bounded one-posting preview (up to three candidates) and can select another owned posting by ID; the dashboard exposes full results.
