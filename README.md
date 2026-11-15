# SkillPilot

A local-first career intelligence MVP for the BuilderWars AWS hackathon. One Strands orchestrator delegates to four real specialist agents, backed by Amazon Bedrock and one DynamoDB table. React dashboards connect assessment evidence, learning, and explainable job matching.

The source architecture is [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). The original document is preserved.

## Run locally

Prerequisites: Python 3.11+, Node 20.19+ (or a supported newer release), npm, and `uv`. Java 17+ enables persistent DynamoDB Local without Docker. This workspace has the dependencies installed in `.venv` and `frontend/node_modules`.

```bash
uv sync --frozen
npm ci --prefix frontend
```

Keep the existing private `.env`. On a new machine, copy `.env.example` to `.env`. Use the AWS SDK credential chain or put temporary organizer credentials only in the ignored `.env` using standard names:

```dotenv
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_SESSION_TOKEN=your-session-token
```

Do not paste credentials into the browser or source code. The AWS CLI is installed in the project environment (`uv run aws --version`); Python scripts load `.env` without printing keys. Bare AWS CLI commands do not load `.env` automatically.

To run persistent local storage, use three terminals from the repository root:

```bash
# Terminal 1: DynamoDB Local, downloaded into ignored .local/ if needed
bash scripts/start_dynamodb.sh
```

```bash
# Terminal 2: create the LOCAL table, then serve the API
uv run python -m scripts.setup_local_db
uv run uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

```bash
# Terminal 3: frontend
npm run dev --prefix frontend
```

Open **http://127.0.0.1:5173**. API documentation: **http://127.0.0.1:8000/docs**. After installation, `bash scripts/dev.sh` starts all three local services in one terminal; Ctrl+C stops the processes it starts. Local data remains in ignored `.local/dynamodb-data/`.

This workspace's private configuration selects Bedrock and DynamoDB Local. For an offline run, set `SKILLPILOT_AI_MODE=mock` and `SKILLPILOT_REPOSITORY=memory` in `.env`, or override them in the backend command. Memory storage resets on process restart. Repository mode is explicit; a failed DynamoDB connection never silently discards data by switching to memory.

## Verify AWS and the agents

```bash
uv run python -m scripts.aws_preflight
uv run python -m scripts.live_agents_smoke
```

The first script verifies CLI/SDK identity, lists Nova models, and makes a tiny Converse inference call. It creates no AWS infrastructure. Reports under `.local/` contain no credential values or account IDs. The second script makes a small number of live inference calls to check actual nested delegation. These calls use Bedrock credits. Offline unit and browser tests use an explicit mock model instead.

## Accounts and presentation actors

The app opens on email/password sign-in. New candidates and employers can create accounts and get their own workspace. Candidates choose their background during onboarding; discovery starts off. Assessments and private records stay attached to the signed-in account.

Three actor accounts are precreated: **Alex Morgan** (`alex@example.com`), **Priya Shah** (`priya@example.com`), and **Jordan Lee** (`jordan@example.com`). Their random initial passwords are stored privately in ignored `.local/actor-accounts.json` after the first backend startup. Open that file locally; do not commit or publish it. These accounts use the same login form as everyone else. The former demo identity selector and passwordless demo endpoints have been removed.

The dashboard focuses on a next step, skill summary, and learning progress. Detailed skills and milestones are in separate tabs. **Ask SkillPilot** opens the assistant when needed. Sign out before signing into another actor's account. See [authentication](docs/AUTHENTICATION.md), [the presenter guide](docs/DEMO_GUIDE.md), and the exact [backend inventory](docs/BACKEND_INVENTORY.md).

## Tests

```bash
uv run pytest -q
npm run build --prefix frontend
# Requires Google Chrome and free ports 8000 / 5173; starts isolated mock services.
npm run test:e2e --prefix frontend
# With DynamoDB Local running:
uv run python -m scripts.local_persistence_smoke
```

Backend tests exercise Strands routing/tool execution, deterministic scoring, profile/evidence isolation, ownership, consent, replay prevention, matching, and repository parity against memory and Moto. The browser tests exercise the complete learning-to-employer flow at desktop and mobile sizes. The optional local persistence smoke test verifies the actual DynamoDB emulator with a separate non-discoverable demo user.

## Implementation

```text
backend/
  api.py                 Thin FastAPI routes and account authentication and sessions
  orchestrator.py        Only user-facing agent; specialists exposed as tools
  agents/                Four specialists, model provider, workflow steering
  tools/                 Deterministic grading, skill normalization, matching
  service.py             Authorized workflow operations and derived views
  db.py                  Memory and single-table DynamoDB repositories
  models.py              Strict Pydantic request/output contracts
  data/jobs.json         Attributed public snapshot and labeled demo roles
  main.py                Prepared AgentCore entrypoint (not deployed)
frontend/src/
  pages/                 Candidate, job marketplace, employer views
  components/            Chat, assessment form, accessible modal
  api.ts                 Typed client contracts
scripts/                 AWS checks, job import, local database helpers
tests/                   Backend verification
deployment/              Prepared image recipe and pinned dependencies
```

All model-facing tools bind the authenticated identity in Python closures. Specialists have limited tool access and return validated structured summaries plus authoritative tool data. The model never supplies assessment scores or writes arbitrary records. Deterministic steering requires data retrieval before a specialist may finalize its response. Budgets limit model-call loops. Model failures return a retryable 503; dashboard actions remain available.

Offline mode is clearly labeled. It supplies deterministic model responses **inside the Strands Model interface**, so the same actual nested agents and tool loops execute. It is not evidence of live Bedrock quality.

## Data and scope

The bundled sample contains 42 public postings across nine employers (including eight public early-career postings) plus six synthetic Northstar Labs roles. URLs and retrieval timestamps are retained. Seven fictional profiles cover engineer, student, employer, and consenting/private comparison candidates; seeded evidence is labeled synthetic. New employer postings are labeled synthetic. Public job skill extraction uses a fixed keyword vocabulary; it may include optional mentions, and original postings must be reviewed. Refresh with `uv run python -m scripts.import_jobs`; it preserves synthetic roles. On backend startup, missing records are added without overwriting profile edits, consent, or evidence. Removed public snapshots leave the active sample while remaining stored.

The sample powers two AI-engineering journeys: a software-engineer transition and a student seeking a first role. Editing the target-role label does not build a new market dataset. Assessments, lessons, and reassessments work; open-ended exercise grading, broad job crawling, email verification/password reset, and production employer verification are outside this MVP.

See [data model and API](docs/DATA_MODEL.md), [AWS/model verification](docs/AWS_SETUP.md), [validation status](docs/VALIDATION.md), and [AgentCore preparation](docs/DEPLOYMENT.md).

## Reference patterns

The application is original SkillPilot code. Patterns were checked against the [AWS workshop](https://github.com/aws-samples/sample-strands-agents-hands-on-workshop): Module 1 for `@tool` agent loops, Module 3 for deterministic workflow enforcement, Module 5 for the runtime wrapper, Module 6 for nested agents exposed as tools, and Module 7 for output and tool-trajectory checks. SDK signatures were verified against the locally installed Strands version and [official SDK reference](https://strandsagents.com/docs/api/python/strands.agent.agent/).

No AWS deployment has been performed. Deployment remains subject to explicit user approval.
