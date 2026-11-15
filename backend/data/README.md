# Demo data provenance

Individual UTC retrieval timestamps and original posting URLs are in `jobs.json`; current counts are in `jobs_manifest.json`.

The active snapshot has **68 real public postings** from nine employer boards and six explicitly synthetic Northstar Labs jobs. All 68 real postings are LLM-tagged with 574 source-grounded tags across 106 skills. Eight public postings have internship or entry/graduate title labels. Jobs cover AI/ML engineering and related platform or research work. Career level is taken from explicit title words; `unspecified` means the title does not establish a level. No education or work-authorization eligibility is inferred.

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

Refresh with `uv run python -m scripts.import_jobs`, then `uv run python -m scripts.tag_jobs`. The importer selects up to ten relevant roles per board, prioritizes early-career titles, deduplicates URLs, preserves synthetic roles and retains prior employer records on API failure. It refuses to replace the snapshot below 50 real jobs. Existing tags survive unchanged descriptions; new/changed postings are tagged by Bedrock. These public API requests require no key. See the official [Greenhouse documentation](https://docs.greenhouse.io/job-board.html) and [Ashby documentation](https://developers.ashbyhq.com/docs/public-job-posting-api). This is a bounded sample, not a market census.

`skill_tags` on real records contains normalized IDs, display labels, required/preferred classifications and exact excerpts checked against the saved description. `tagging_model`, `tagged_at` and `tagged_description_hash` record provenance. `required_skills` uses required tags; if all tags are preferred, it uses that tracked set while preserving the preferred labels. Counts and matching are deterministic over this set. Source text is capped at 12,000 characters; follow the original URL for full requirements. The six synthetic fixtures retain explicit requirements; newly created employer postings are analyzed dynamically.

`demo_profiles.json` contains seven fictional identities. The comparison profiles' `seed_scores` are synthetic fixtures graded through the same deterministic code and labeled as seeded evidence. The interactive software engineer and student start with no seed scores. Actual form submissions replace current skill evidence with a server-graded record marked non-synthetic. Nothing here is a scraped real-person resume.

Seeding fills missing profiles, fixtures and jobs while preserving edits, consent and assessed records. Startup imports new snapshot IDs and refreshed LLM-tagged public records. Removed public snapshots remain stored for history but leave the active sample. Employer-owned postings are preserved.
