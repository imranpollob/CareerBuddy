# Adaptive career workflow

## Signup and skill discovery

Signup collects name, email, password and candidate/employer purpose. New candidates enter conversational onboarding. The Strands orchestrator uses Bedrock to ask one question at a time, adapting to previous answers. It discovers role, goal, projects and tools rather than requiring a fixed skill list.

After two to six answers, the candidate reviews proposed skills with supporting answer excerpts. Every excerpt must occur in the supplied answers. Confirmation accepts only a revision number, then atomically saves server-held claims and profile. A stale browser cannot overwrite a newer conversation. Claimed skills are editable context and never assessment evidence. Conversations and private labels remain owner-scoped.

## Personalized assessment and coaching

After confirmation, Assessment uses a short-lived Strands invocation with role, claims, project excerpts, target requirements and prior prompts to create four original objective questions. Pydantic validates topic, IDs, distinct options, answer indices and explanations. A pending attempt and separate private key are written together only after generation succeeds.

The browser receives questions and choices, never the key. Submission supplies choices only. Python grades against the stored key, writes the result and current skill evidence atomically, and rejects replay. A 75% pass supplies limited knowledge-check evidence. Users cannot supply scores or directly alter evidence. Model-authored questions can be imperfect; these checks are not certification.

Roadmaps compare assessment evidence with job tags. Coach generates a personal lesson and exercise for the next gap. Practicing a lesson prepares fresh generated reassessment; practice alone creates no assessed skill. Failed later assessments replace current evidence while preserving history.

## Real job data

The project includes 68 real postings from free Greenhouse/Ashby employer APIs. Each has a URL, retrieval timestamp, saved description, model provenance and source-grounded skill tags. Bedrock distinguishes required/preferred skills. The validator drops excerpts absent from the source and refuses an entirely ungrounded analysis. All 68 saved postings are tagged. New employer postings pass through the same analysis before saving.

```bash
uv run python -m scripts.import_jobs
uv run python -m scripts.tag_jobs
```

The importer enforces a 50-job minimum and preserves tags for unchanged descriptions. Tagging checkpoints successful batches and retries failures individually. Both update `backend/data/jobs_manifest.json`. Restart the API to sync the snapshot into the local table.

## Modes and failures

Bedrock mode uses Amazon Nova 2 Lite through Strands. Mock mode uses labeled deterministic interview/question/lesson fixtures. There is no silent mock fallback on inference failure. Generation errors return retryable 503 responses and preserve saved progress. No deployment or paid AWS resource creation is required; inference uses permitted account credits.

The agents-as-tools architecture remains: five agent roles and nine custom tools. Authoring tasks reuse those roles through typed Strands calls. Matching, scoring, ownership and consent checks remain deterministic Python.

## CareerBuddy roadmap and passport

Candidates now land on persistent AI Chat. Profile, Learning, Assessments and Jobs have separate navigation. A saved six-skill career path is built from current sampled requirements; opened paths remain stable while unstarted focus slots can adapt to demand. Each expanded skill receives three generated competencies. Lessons and objective assessments target those objectives, and last activity is saved for continuation.

Competency evidence stays separate from whole-skill evidence. All three passes support a Foundational aggregate; a later failed competency invalidates that aggregate. Revision guards prevent concurrent topic submissions from losing aggregate progress. The Skill Passport exposes dates, scope, assessment references and feedback, while Applied and Demonstrated remain later practical-assessment levels. See [CareerBuddy status](CAREERBUDDY_IMPLEMENTATION.md).
