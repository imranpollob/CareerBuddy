# SkillPilot hackathon demo

Three requested stories share one platform. A fourth demonstration moment connects them: learning and reassessment change the evidence used by the marketplace.

Start from the repository root with `bash scripts/dev.sh`, then open http://127.0.0.1:5173. Sign in with an email and password. Initial actor credentials are in the private `.local/actor-accounts.json` file. Alex (`alex@example.com`), Priya (`priya@example.com`), and Jordan (`jordan@example.com`) are regular precreated accounts. Sign out before signing into another account; no identity switcher is exposed. New users can sign up through the same application.

## 1. Software engineer transitioning to AI engineering

**Person:** Alex Morgan, Software Engineer → AI Engineer.

1. Sign in as **Alex Morgan**. Show the current role, goal, self-reported Python/SQL, and applied-AI portfolio project.
2. Open **Ask SkillPilot** and ask **“What skills are in demand?”** Expand the delegation trace to show Job Market retrieving the sample and computing skill counts.
3. Ask **“Build my learning roadmap.”** Coach reads Alex's own evidence and job requirements.
4. Open a Python or RAG assessment. Submit answers through the form; show that a profile edit cannot set an assessed score.
5. Open **Find jobs** and compare the supported skills and gaps on **Applied AI Engineer** or **AI Backend Engineer · RAG**.

**Message for judges:** existing engineering experience provides context, while demonstrated AI fundamentals guide the next learning steps. Claims alone never count as evidence.

## 2. Student seeking a first AI engineering role

**Person:** Priya Shah, Computer Science Student → AI Engineer.

1. Sign in as **Priya Shah**. Priya has her own profile, assessments, lessons, consent, and chat session.
2. Show the Python/SQL-first roadmap and the campus study-assistant portfolio project.
3. Ask **“I am a computer science student seeking my first AI engineering role. Build my learning roadmap.”**
4. Complete a fundamentals assessment. Visit **Find jobs**, which defaults to **Internships + entry / graduate** for Priya.
5. Compare a real sourced opportunity with the clearly labeled **AI Engineering Intern** and **Junior AI Engineer** demo roles.
6. Opt into discovery using **Edit profile** if you want to show Priya in the employer view. Discovery starts off.

**Message for judges:** student guidance starts with foundations and a portfolio, and the job view emphasizes early-career opportunities. Stage labels come from titles; a posting may still require a particular degree, location, work authorization, or experience. Skill coverage is not eligibility.

## 3. Employer matching candidates to an AI role

**Person:** Jordan Lee, demo hiring manager.

1. Sign in as **Jordan Lee** and choose **Junior AI Engineer**.
2. Compare the initial seeded profiles:

| Demo profile | Background | Evidence supporting this posting | Gaps |
| --- | --- | --- | --- |
| Sam Rivera | Backend engineer with applied AI fundamentals | Python, LLM, RAG: 3 of 4 | SQL |
| Casey Brooks | Software engineer transitioning to AI | Python, SQL: 2 of 4 | LLM, RAG |
| Maya Chen | Final-year CS student | Python, SQL: 2 of 4 | LLM, RAG |

3. Expand each evidence panel to show the assessment reference, date, scope, and **Seeded synthetic evidence** label.
4. Alex or Priya appears only after passing a relevant assessment and opting in. Their newly submitted evidence is labeled **Assessment-backed evidence**.
5. Create an AI Engineer posting, specify career level and describe its requirements. Click **Analyze and save posting**; Bedrock identifies its skills automatically. Compare its consenting candidates.

Taylor Reed is a deliberately private synthetic profile and must never appear in employer discovery. There are no opaque hiring scores, personality inferences, or automatic hiring decisions.

## 4. Learning changes the match

Use either candidate identity:

1. Record the current coverage for a chosen demo job.
2. Take an assessment with gaps, read its lesson, and practice the exercise.
3. Click **I’ve practiced · Start reassessment** and submit a fresh attempt.
4. Show the changed evidence and matching requirements. For example, a new Python pass adds one supported skill to the AI Engineering Intern role.
5. Show the same evidence in the employer view after explicit opt-in.

Reading a lesson alone never changes assessed skills. In Bedrock mode reassessment generates fresh questions using personal context and prior prompts. Offline mode uses labeled fixtures. A failed later attempt removes the skill from current passing evidence; previous attempts stay in history.

## Data and reliable presentation

- The snapshot contains **68 public postings across 9 employers**, including **8 public internship/entry postings**, plus **6 synthetic demo jobs**. Public roles include AI engineering, ML, research engineering, and related AI-platform opportunities.
- The seven profiles are synthetic: two interactive candidates, one employer, three consenting comparison candidates, and one private comparison candidate.
- All 68 public postings have Bedrock-generated skills: **574 tags across 106 skills**. Expand posting details for required/preferred labels and exact source excerpts. URLs, retrieval dates, model and description hashes are saved with each posting.
- Real postings provide context. Synthetic Northstar jobs give the presentation stable, explicit requirements, even if a public vacancy closes.
- Run `uv run python -m scripts.aws_preflight` before presenting. A labeled mock mode is available if temporary credentials expire.
- Existing local profile edits, consent, and assessment records are preserved on restart. Do not delete the local database to restart a presentation; use fresh assessment attempts and sign into the desired actor account.


## New-user demonstration

The product is not limited to presentation actors. Choose **Create an account** and enter name, email, password and account purpose. For a new candidate:

1. Answer the first question in your own words, for example that you are a software engineer or CS student seeking AI engineering work.
2. Describe a project, tools you personally used and your responsibilities. Follow-up questions adapt to those answers in Bedrock mode.
3. Review discovered skills and expand their supporting answer excerpts. Correct anything before confirming. Claims are not assessed evidence.
4. Confirm to generate a personalized four-question assessment. Submit it to persist server-graded evidence.
5. Explore **My skills**, **Learning plan**, and **Find jobs**. Ask the coach for guidance and open a missing-skill lesson.

Existing actors have prefilled backgrounds and skip initial onboarding. They still receive generated assessments and lessons in Bedrock mode. Check the mode badge before presenting: offline preview uses labeled fixtures.
