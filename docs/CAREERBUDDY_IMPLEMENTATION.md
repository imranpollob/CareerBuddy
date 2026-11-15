# CareerBuddy implementation status

The supplied [feature plan](CAREERBUDDY_FEATURES.md) is preserved. CareerBuddy is the user-facing brand; the existing single-table SkillPilot backend, temporary AWS configuration and three regular actor accounts remain compatible. Nothing is deployed.

| Plan priority | Delivered behavior |
| --- | --- |
| AI chat / orchestrator | Candidate landing page; four suggested actions; selective real Strands delegation; private conversation history across login/restart |
| Profile and dream job | Current/target roles, three career purposes, adaptive onboarding, self-reported skills and opt-in |
| Market analysis | 68 real, attributed, LLM-tagged public postings with required/preferred source excerpts |
| Visual roadmap | One saved six-skill career path; refreshes unstarted focus slots from demand while preserving opened paths; interactive connected competency steps |
| Skill breakdown | Three generated progressive knowledge/scenario competencies per expanded skill |
| Lessons | Click-to-generate explanation, worked examples, takeaways, practice and assessment; cached privately; resume last activity |
| Competency assessment | Generated objective questions scoped to a learning objective, immutable server-held keys, deterministic grading, retry and feedback |
| Skill progress / passport | Latest evidence, results, dates, scope, supporting assessment references, strengths, practice gaps and full attempt history |
| Candidate matching | Assessment-backed supported/missing job skills and original application links; claims do not count as evidence |
| Employer target | Create/analyze postings, inspect opted-in profiles and relevant evidence; separate role workspace |

## Evidence rules

A single narrow competency pass does not establish the whole skill. All three competency passes support Foundational skill evidence; a later failed topic invalidates that aggregate. Concurrent submissions use path revisions and pending-attempt conditions in the same transaction. Standalone broad skill checks also support limited Foundational evidence. Historical attempts remain intact.

Not Assessed, Foundational, Applied and Demonstrated are visible in the passport. The last two are explicitly marked for later practical assessments. Objective scenario questions test reasoning; they do not prove completed coding work or a project. Users cannot edit mastery or assessment-backed scores.

## Later scope from the plan

Scheduled reminders, sandboxed coding exercises, explain-a-concept grading, mini projects/final challenges and the associated Applied/Demonstrated levels are not implemented. Employer invitations and full hiring workflows are also deferred. No email is sent. AgentCore deployment still requires explicit approval.

The sourced sample remains focused on AI engineering and related roles. Changing a dream-job label personalizes generation but does not automatically collect a different occupation's dataset. AI-authored content can be imperfect; source excerpts and assessment scope remain inspectable.

## Verification

Use the README commands for pytest, TypeScript/Vite and browser tests. The browser flow covers chat persistence, generated competency paths, lessons, failure/retry, all-three-topic aggregation, passport, job matching, opt-in employer discovery and new-user onboarding at desktop/mobile sizes.

With DynamoDB Local running, `uv run python -m scripts.career_path_smoke` verifies real Bedrock path/lesson/question generation, private answer keys, persisted competency evidence without overstating broad mastery, Coach delegation and saved conversation. It uses an opted-out temporary profile and removes only its own records in a finally block. Safe reports stay in ignored `.local/`.
