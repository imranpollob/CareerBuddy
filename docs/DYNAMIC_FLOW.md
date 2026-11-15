# Adaptive career workflow

## Signup and skill discovery

Signup collects name, email, password and candidate/employer purpose. Candidates answer exactly four numbered questions: current role, highest education, work experience (0–30 years), and self-reported expertise (Beginner, Intermediate, Advanced, Expert). Education uses standard predefined choices. A review screen confirms the answers without asking additional questions.

The server validates choices, persists progress and rejects stale revisions or a fifth answer. Confirmation saves the background fields to the signed-in profile atomically. Background does not create skill claims or assessment evidence. These questions need no model inference, so onboarding remains available during a model outage. Incomplete older interviews restart in the bounded flow; completed profiles remain unchanged.

New accounts start with empty Home and Learning views, zero verified skills and no assessment attempts. GET /learning never initializes a plan for a fresh user. Older automatic shortlists with no generated paths remain hidden. Completing onboarding saves background only; it does not launch an assessment.

The explicit Create my roadmap action calls POST /learning, selects target-role requirements and generates the first personalized competency path through Coach. Generation failure leaves the account empty and retryable. Detailed content remains user-scoped. Progress totals count only generated competencies, rather than assuming three for every suggested skill. Public postings remain available on the Jobs page; they are shared job-market data, not another candidate’s history.


## Personalized assessment and coaching

After confirmation, Assessment uses a short-lived Strands invocation with profile background, target requirements and prior prompts to create four original objective questions. Pydantic validates topic, IDs, distinct options, answer indices and explanations. A pending attempt and separate private key are written together only after generation succeeds.

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

Candidates now land on Home, which displays saved progress and one actionable next step without a model call. AI Chat is a separate conversation page. Learning, Assessments and Jobs have dedicated navigation; My Profile is by the account controls. A saved six-skill career path is built from current sampled requirements; opened paths remain stable while unstarted focus slots can adapt to demand. Each expanded skill receives three generated competencies. Lessons and objective assessments target those objectives, and last activity is saved for continuation.

Competency evidence stays separate from whole-skill evidence. All three passes support a Foundational aggregate; a later failed competency invalidates that aggregate. Revision guards prevent concurrent topic submissions from losing aggregate progress. The Skill Passport exposes dates, scope, assessment references and feedback, while Applied and Demonstrated remain later practical-assessment levels. See [CareerBuddy status](CAREERBUDDY_IMPLEMENTATION.md).
