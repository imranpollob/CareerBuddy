# CareerBuddy backend inventory

## Five real Strands agents

| Agent | Purpose | Application-defined tools available |
| --- | --- | --- |
| SkillPilot Orchestrator | User conversation and selective delegation | Four specialist delegation tools plus `get_profile` |
| Job Market Intelligence | Read sourced jobs and explain counted skill requirements | `analyze_job_requirements` |
| Skill Assessment | Prepare the signed-in candidate's objective assessment | `prepare_skill_assessment` |
| Skill Coach | Read personal evidence and generate/explain learning guidance | `get_learning_plan` |
| Marketplace | Retrieve job matches or consenting candidates for owned postings | `get_marketplace_matches` |

There are **9 custom Strands tools**: 4 delegation wrappers + 1 profile tool + 4 specialist tools. The SDK also provides structured-output machinery for each specialist's `Summary` schema; those formatting helpers are not extra business tools. Ordinary FastAPI routes, password helpers, Python grading functions, and repository methods are not counted as agents or agent tools.

In Bedrock mode all five use real Strands `Agent` instances with Nova 2 Lite. Specialists are instantiated only when delegated to; they are not five independent services. In explicit mock mode, a deterministic provider replaces inference while exercising the same nested Strands agent/tool loops. Live delegation has been verified separately from mock tests.

Grading and matching are deterministic Python. The Assessment specialist prepares an assessment; it does not grade arbitrary chat assertions. Only a validated form submission updates evidence. Job collection is a manual script, not a live browsing agent tool. Models explain computed market frequencies and matches rather than inventing them.

## Bundled application datasets

| Data | Count | Provenance |
| --- | --- | --- |
| Public job postings | 68 | Nine employer boards, original URLs and retrieval dates retained; all LLM-tagged |
| Synthetic job postings | 6 | Stable presentation fixtures with explicit skill requirements |
| Public early-career postings | 8 | Seven internship titles and one entry/graduate title; subset of the 68 |
| Fictional profiles | 7 | Two candidate actors, one employer actor, three consenting comparison candidates, one private comparison candidate |
| Precreated login accounts | 3 | Actor accounts only; additional users can sign up |
| Seeded comparison assessments | 13 | Synthetic fixtures across four comparison profiles; explicitly labeled |
| Job skill tags | 574 | Bedrock-generated required/preferred tags, each with a validated source excerpt |
| Distinct job skills | 106 | Normalized tags in the saved real-job sample |
| Reference assessment questions | 28 | Seven fixed topics for offline fixtures and synthetic seed evidence only |
| Reference lessons/exercises | 7 | Offline fixtures; Bedrock generates personalized lessons in live mode |
| Live assessments | Generated on demand | Four personalized objective questions; private keys, deterministic grading |
| Onboarding interviews | Generated on demand | Adaptive questions and user-confirmed skill claims grounded in answers |

The nine public employers are Anthropic, Scale AI, Databricks, Figma, Hex, Cohere, Ramp, Perplexity, and Baseten. Collection uses free Greenhouse and Ashby APIs. Bedrock distinguishes required/preferred skills and exact excerpts are checked against the saved description before accepting tags. This bounded sample is not a representative market census; postings can close. Career-stage labels do not establish eligibility.

Structured authoring reuses the same five role definitions: the orchestrator interviews candidates, Assessment authors questions, Job Market tags postings, and Coach writes lessons. Each task creates a short-lived Strands invocation; these are not additional agent roles or extra custom tools. The **5 agent roles / 9 custom tools** count remains unchanged.

These are application data and fixed learning content, not a model-training dataset. New signups, employer-created jobs, assessment attempts, roadmaps, and matches are runtime records and increase independently of the bundled counts.

Source files: `backend/data/jobs.json`, `backend/data/demo_profiles.json`, `backend/tools/assessments.py`, and `backend/tools/jobs.py`.

CareerBuddy adds persisted private chat history, one saved career path, generated three-topic competency breakdowns, structured lessons, competency evidence and a Skill Passport. These are workflow operations using the same five Strands roles and nine custom tools, not additional agents. Scheduled learning reminders and practical coding/project mastery levels remain later scope.
