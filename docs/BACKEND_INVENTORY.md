# Backend inventory

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
| Public job postings | 42 | Nine employer boards, original URLs and retrieval dates retained |
| Synthetic job postings | 6 | Stable presentation fixtures with explicit skill requirements |
| Public early-career postings | 8 | Seven internship titles and one entry/graduate title; subset of the 42 |
| Fictional profiles | 7 | Two candidate actors, one employer actor, three consenting comparison candidates, one private comparison candidate |
| Precreated login accounts | 3 | Actor accounts only; additional users can sign up |
| Seeded comparison assessments | 13 | Synthetic fixtures across four comparison profiles; explicitly labeled |
| Skills / assessment topics | 7 | Python, SQL, LLM applications, RAG, PyTorch, AWS/Bedrock, AI evaluation |
| Objective assessment questions | 28 | Four fixed questions per topic, server-held answer keys |
| Lessons and exercises | 7 | One working learning/reassessment cycle per topic |

The nine public employers are Anthropic, Scale AI, Databricks, Figma, Hex, Cohere, Ramp, Perplexity, and Baseten. This is a bounded convenience sample, not a representative market census. Skill extraction uses keyword mentions and can include optional/contextual text. Career-stage labels do not establish educational or work-authorization eligibility.

These are application data and fixed learning content, not a model-training dataset. New signups, employer-created jobs, assessment attempts, roadmaps, and matches are runtime records and increase independently of the bundled counts.

Source files: `backend/data/jobs.json`, `backend/data/demo_profiles.json`, `backend/tools/assessments.py`, and `backend/tools/jobs.py`.
