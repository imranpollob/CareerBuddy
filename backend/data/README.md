# Demo data provenance

Snapshot collected on November 14, 2026 (America/Detroit). Individual UTC retrieval timestamps and original posting URLs are in `jobs.json`.

The active snapshot has 42 public postings from nine employer boards and six explicitly synthetic Northstar Labs jobs. Eight public postings have internship or entry/graduate title labels. Jobs cover AI/ML engineering and related platform or research work. Career level is taken from explicit title words; `unspecified` means the title does not establish a level. No education or work-authorization eligibility is inferred.

Public sources:

| Employer | Board |
| --- | --- |
| Anthropic | [Greenhouse](https://boards-api.greenhouse.io/v1/boards/anthropic/jobs?content=true) |
| Scale AI | [Greenhouse](https://boards-api.greenhouse.io/v1/boards/scaleai/jobs?content=true) |
| Databricks | [Greenhouse](https://boards-api.greenhouse.io/v1/boards/databricks/jobs?content=true) |
| Figma | [Greenhouse](https://boards-api.greenhouse.io/v1/boards/figma/jobs?content=true) |
| Hex | [Ashby](https://api.ashbyhq.com/posting-api/job-board/hex) |
| Cohere | [Ashby](https://api.ashbyhq.com/posting-api/job-board/cohere) |
| Ramp | [Ashby](https://api.ashbyhq.com/posting-api/job-board/ramp) |
| Perplexity | [Ashby](https://api.ashbyhq.com/posting-api/job-board/perplexity) |
| Baseten | [Ashby](https://api.ashbyhq.com/posting-api/job-board/baseten) |

Refresh with `uv run python -m scripts.import_jobs`. The importer selects up to five relevant roles per board, prioritizes early-career title labels, preserves synthetic roles, and retains that employer's prior records if its API fails. This is a bounded convenience sample, not a market census. Multiple locations/reqs may share a title.

`required_skills` on sourced records means normalized keyword mentions from the description, which may include optional or company-wide context. Displayed counts are computed from those mentions. On synthetic employer postings it means the demo employer's explicit selections. Source text is capped at 12,000 characters; follow the original URL for the full posting.

`demo_profiles.json` contains seven fictional identities. The comparison profiles' `seed_scores` are synthetic fixtures graded through the same deterministic code and labeled as seeded evidence. The interactive software engineer and student start with no seed scores. Actual form submissions replace current skill evidence with a server-graded record marked non-synthetic. Nothing here is a scraped real-person resume.

Seeding is additive: it fills missing profiles, fixtures, and jobs while preserving existing edits, consent, and assessed records. Removed public snapshots remain stored for historical use but are excluded from the active job sample. Startup imports newly added snapshot IDs; existing job content is not automatically overwritten.
