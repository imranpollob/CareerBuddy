# CareerBuddy presenter guide

Start `bash scripts/dev.sh`, then open http://127.0.0.1:5173. Use your own signup accounts. No sample identities or fictional evidence are loaded by default.

Create a candidate account for each career scenario you want to present, and a separate employer account. Complete onboarding and submit assessments with those accounts before presenting saved progress. Sign out before switching accounts.

## Candidate career loop

1. Sign up or sign in to your candidate account. Answer onboarding questions and confirm the discovered skills. **Home** opens with the career goal, a recommended next action, roadmap/passport snapshots and sourced jobs. Open **AI Chat** and ask **Evaluate my profile**; expand the trace to show actual Coach delegation. Reload to show saved conversation history.
2. Open **Learning**. Generate your roadmap and expand a skill into three competencies, each with a specific objective. The path uses your profile and the real-job sample.
3. Open a competency lesson. Show concept, examples, key takeaways and practice. Click **I've practiced · Start assessment** (the UI uses a typographic apostrophe) or **Check understanding** on the topic.
4. Submit the four objective questions. The browser never receives the pending answer key. A failed attempt offers feedback and reassessment. One topic pass changes competency progress, not the entire skill.
5. Complete all three topic checks to establish Foundational evidence for the broader skill. Open **Assessments** to inspect the **Skill Passport**, dates, scope, attempt references, strengths and practice gaps. Applied/Demonstrated are explicitly marked for later practical assessments.
6. Open **Jobs** and compare supported/missing skills. Inspect a real posting's required/preferred tags and exact source excerpts, then open its original application URL.
7. Return to **Home** or **Learning** and use the next-step controls to resume a pending assessment or the next topic.

Broad skill checks also remain available through the passport. They provide limited Foundational evidence. Lesson practice alone never changes assessed skills. A failed later competency invalidates skill evidence aggregated from that path; history remains intact.

## Employer evidence

In the candidate's **My Profile** beside the account controls, explicitly enable discovery and save. Sign out, sign in to your employer account, and create a relevant posting. The candidate appears only with passing relevant evidence and current consent. Inspect references, dates and evidence scope.

Create a job by entering title, company, level and description. **Analyze and save posting** dynamically identifies skills before matching. Candidates with discovery disabled must never appear. There are no opaque hiring scores or automatic hiring decisions. No invitations or email are sent.

## New user

Choose **Create an account**, enter name/email/password/account purpose, then answer the adaptive onboarding interview. Describe real projects and the tools personally used. Review answer-grounded skill claims and confirm; CareerBuddy generates a personalized assessment. Close or complete it to enter Home. Discovery starts off. Career purpose can be updated in **My Profile**: stay relevant, find a new job, or switch careers.

## Data and operating notes

- The active dataset contains 68 real postings from nine employers, all LLM-tagged: 574 source-grounded tags across 106 skills.
- Fictional profiles, jobs and comparison attempts are disabled by default and available only to isolated tests. Normal submissions are server-graded.
- Bedrock mode uses Nova 2 Lite. Offline mode is visibly labeled and uses deterministic fixtures, including reference questions. A mock pass is not live model-quality evidence.
- The sample focuses on AI engineering and related roles. Stage labels do not establish eligibility, and public vacancies can close.
- `uv run python -m scripts.career_path_smoke` verifies real generation/persistence against DynamoDB Local, then removes its temporary profile. Reports/screenshots stay private in `.local/`.
- See [implementation status](CAREERBUDDY_IMPLEMENTATION.md) for later scope. Nothing has been deployed to AWS.
