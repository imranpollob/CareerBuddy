# CareerBuddy MVP validation

Validated locally with explicit mock tests plus separate actual Bedrock/DynamoDB Local integration checks.

| Area | Status and evidence |
| --- | --- |
| Accounts | Email/password signup, no default sample accounts, Argon2 hashing, expiring/revocable persisted sessions and account isolation; disabled fixture logins/sessions rejected |
| Adaptive onboarding | Bedrock asks follow-ups, extracts answer-grounded claims, and saves a revision-guarded review/confirmation; resumes across reloads |
| Real job data | 68 public postings from nine employers active by default; synthetic jobs and fictional profiles confined to opt-in test fixtures |
| Dynamic skill tags | All 68 public postings tagged by Nova 2 Lite: 574 tags across 106 skills; required/preferred status, exact validated excerpts and model/hash provenance |
| Dynamic assessment | Personalized four-question objective checks, strict output validation, separate private keys and deterministic grading; client scores rejected |
| Evidence persistence | Memory and single-table DynamoDB implementations; atomic submission, replay protection and conditional interview updates |
| Coaching | Evidence/market gaps, prioritized roadmap, personalized lesson/exercise and fresh generated reassessment |
| Matching | Explainable supported/missing skills; only passed assessment evidence counts |
| Employer marketplace | Analyze/tag a new posting, enforce ownership, inspect only consenting candidates and relevant evidence |
| Multi-agent system | One Strands orchestrator and four specialists exposed as tools; typed summaries and observable delegation results |
| Live Bedrock flow | Actual adaptive interview → confirmed skills → personalized Python assessment → server grading/persisted evidence → generated FastAPI lesson → Coach delegation reading the new evidence |
| Offline AI | Explicit configuration with fixture provenance retained in records/API; actual Strands agent/tool loops remain in use |
| Backend checks | 67 pytest tests passed; covers routing, scoring, persistence, matching, authentication, consent, sample-account removal/defaults, generation failure and claim/tag grounding |
| Browser checks | Six browser tests at desktop and iPhone sizes; adaptive signup plus assessment → learning → reassessment → marketplace/employer flow |
| Frontend build | TypeScript and Vite production build passed |
| AgentCore preparation | Local runtime entrypoint previously tested; image recipe prepared, nothing deployed |

The live assessment response contained no answer key; server grading persisted a passing result in actual DynamoDB Local. A private safe report is in `.local/dynamic-flow-report.json`. Public provenance and counts are reproducible in `backend/data/jobs_manifest.json`. Live checks and scripts create no cloud infrastructure.

Tests reject unsupported interview claims, ungrounded job tags, client-supplied scores, stale revisions, replayed submissions, foreign record access, opt-out discovery and unrelated cross-origin writes. Generation failure writes neither a public assessment nor a private key. Inference errors preserve saved interview progress and return retryable 503 responses.

The browser flow takes a failing assessment, practices a lesson, passes a fresh attempt, checks increased requirement coverage, opts into discovery, inspects evidence as an employer, and creates another posting. Mock responses are fixtures, not a measure of live model quality. AI-authored questions are short knowledge checks, not certification; factual quality is not guaranteed by schema validation. There is no paid LLM-as-judge suite by default.

MVP boundaries:

- AI-engineering sample with related platform/research roles; editing a goal does not collect another role-specific dataset.
- Public snapshots can close and represent a bounded employer sample. Tags are model interpretations with inspectable source excerpts.
- Exercises are practice, not open-ended graded assignments or proctored examinations.
- Email verification, password reset, MFA, independent employer verification and distributed rate limiting are outside scope.
- Refresh is manual. Restart loads new public snapshots/tags while preserving profiles, consent and evidence.
- Docker image build, remote AgentCore identity integration and AWS deployment remain unperformed.

Use the README commands to rerun verification, especially when temporary credentials change. No AWS resources have been created.

CareerBuddy validation also covers career-purpose updates, saved visual paths, generated competencies, private structured lessons, narrow-topic grading, all-three-topic aggregation, failed reassessment invalidation, concurrent submissions, persistent chat across login/API restart, and memory/DynamoDB repository parity. The live Nova competency check passed path generation, explanation/examples/takeaways/practice, assessment generation with private keys, persisted partial evidence, Coach delegation and text history. Its temporary profile was removed.

The interface now uses a Linear-inspired dark default theme with a light alternative, locally bundled Inter/JetBrains Mono fonts, and sidebar account controls instead of a top bar. Chat and lessons render Markdown. Browser checks cover semantic headings/lists/tables, code copying, rejection of unsafe links/raw HTML/images, visible pending-generation loaders, error recovery and reduced-motion behavior. Loader messages rotate without presenting fabricated percentages.

Home checks verify the default candidate landing page, no generation requests on load/reload, pending-assessment resume without regeneration, updated skill/competency snapshots after grading, featured-role detail navigation and mobile account/profile access. The existing conversation-history, Markdown, loader/error and employer flows still run at both desktop/mobile sizes.

Customer-facing generation/provider badges and the chat header/footer have been removed. Normal startup excludes sample profiles, postings and evidence. Underlying generation/model provenance is retained in persisted records and API responses.
