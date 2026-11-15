# **SkillPilot — Hackathon Architecture (MVP)**

BuilderWars 2026 | AWS AI Architecture Track | 3-Person Team

**Goal:** Build a working multi-agent career intelligence platform that evaluates skills, recommends learning paths, and connects candidates with employers through a two-sided marketplace.

We will keep the architecture simple enough to build during the hackathon while demonstrating meaningful use of Amazon Bedrock, Strands Agents, and AWS infrastructure.

## **1. Final technology stack**

| Layer         | Technology               | Purpose                            |
| ------------- | ------------------------ | ---------------------------------- |
| Frontend      | React + Tailwind CSS     | Candidate and employer interfaces  |
| Backend       | Python + FastAPI         | API and request handling           |
| AI models     | Amazon Bedrock           | LLM inference                      |
| Multi-agent   | Strands Agents SDK       | Orchestration and delegation       |
| Agent hosting | Amazon Bedrock AgentCore | Deploy the multi-agent application |
| Database      | Amazon DynamoDB          | All application data               |
| Job data      | Public job APIs          | Retrieve current job postings      |

**What we're deliberately avoiding:** S3, OpenSearch, vector databases, SageMaker, Step Functions, Kubernetes, and unnecessary microservices.

For the live demo, FastAPI can run locally as a thin backend that invokes the deployed AgentCore application through AWS credentials held on the server, never in the browser. AWS documents this runtime invocation mechanism.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

Boto3 1.44.3 documentation



## **2. Complete architecture**

**SkillPilot Web Application**

Candidate Dashboard • Employer Dashboard • AI Chat

**FastAPI Backend**

Requests • Demo identities • API integration

AWS BEDROCK AGENTCORE RUNTIME

**SkillPilot Orchestrator**

Conversation • Routing • Delegation

Job Market Agent

What employers need

Skill Assessment Agent

What the candidate knows

Skill Coach Agent

What to learn next

Marketplace Agent

Which opportunities fit

**Amazon Bedrock**

Foundation models power agent reasoning

**Amazon DynamoDB**

One database for users, skills, jobs, assessments, roadmaps and matches

All five agents run in **one Strands application**, hosted on one AgentCore Runtime. The orchestrator invokes the four specialists as tools, without requiring independent agent deployments.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://strandsagents.com\&sz=32)

Strands Agents



## **3. Agent design**

We will implement **one orchestrator + four focused specialist agents**.

| Agent                 | Responsibility                                              | Main tools                                    |
| --------------------- | ----------------------------------------------------------- | --------------------------------------------- |
| **Orchestrator**      | Understand requests, communicate with users, delegate tasks | Specialist agents, `get_profile()`            |
| **Job Market Agent**  | Extract and summarize skills required by employers          | `search_jobs()`, `analyze_job_requirements()` |
| **Assessment Agent**  | Ask questions and evaluate demonstrated knowledge           | `create_assessment()`, `grade_assessment()`   |
| **Skill Coach Agent** | Compare skill gaps and guide learning                       | `get_skill_gaps()`, `generate_roadmap()`      |
| **Marketplace Agent** | Recommend jobs and discover opted-in candidates             | `match_jobs()`, `find_candidates()`           |

Each specialist has its own system prompt and limited tool access.

### **3.1 Orchestrator**

The only agent that directly interacts with users and employers.

Example:

> User: "I am a software engineer and want to move into AI engineering."

The orchestrator coordinates the Job Market Agent and Assessment Agent, then asks the Coach for a roadmap.

It can return preliminary recommendations immediately rather than waiting for every agent when the request is simple.

### **3.2 Job Market Agent**

Maintains job-market intelligence.

Responsibilities: retrieve postings, extract skill requirements, standardize skill names, and identify recurring requirements.

For the MVP, use approximately 10–20 relevant job postings from supported public sources, retaining URLs and retrieval timestamps.

**Important:** Actual skill frequency is calculated by Python, not guessed by the LLM.

### **3.3 Assessment Agent**

Evaluates the candidate's skills.

For the hackathon, use a small assessment containing 3–5 questions focused on one topic. The model can generate explanations and feedback, while a deterministic grading function evaluates questions with objective answers.

Example: the user claims Python experience, completes an assessment, and receives a recorded result.

Assessment records cannot be edited by the candidate through normal profile updates.

### **3.4 Skill Coach Agent**

Combines market requirements and assessment results.

Example:

**Target: Applied AI Engineer**

1. Strengthen Python fundamentals where needed
2. Learn PyTorch fundamentals
3. Build a small LLM application
4. Practice RAG implementation
5. Complete a practical reassessment

Illustrative roadmap. Actual milestones depend on the user's assessment and sourced job requirements.

For the demo, one learning milestone and one reassessment are enough to demonstrate the coaching loop.

### **3.5 Marketplace Agent**

The marketplace supports two modes.

**Candidate-side marketplace**

Find suitable job openings, show matched requirements, and identify remaining skill gaps.

**Employer-side marketplace**

Publish a job, discover opted-in candidate profiles, and review assessment-backed evidence.

Use simple matching logic for the hackathon. The AI explains the results, while deterministic Python compares job requirements with available skill evidence.

For example, "3 of 5 required skills supported by assessment evidence" is an understandable coverage measure, not a hiring prediction.

## **4. One DynamoDB database**

Use a single table named `SkillPilot`.

| Entity     | Example data                                         |
| ---------- | ---------------------------------------------------- |
| User       | User ID, name, current role, target role, visibility |
| UserSkill  | Skill ID, claimed level, assessment-backed level     |
| Job        | Job ID, employer, title, required skills, source     |
| Assessment | Questions, answers, result, evidence, date           |
| Roadmap    | User ID, milestones, completion status               |
| Match      | User ID, job ID, matching evidence                   |

DynamoDB supports a single-table approach using a partition key and sort key.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

Amazon DynamoDB



A simple key design:

```
PK = USER#123    SK = PROFILE
PK = USER#123    SK = SKILL#python
PK = USER#123    SK = ASSESSMENT#001
PK = USER#123    SK = ROADMAP#001

PK = JOB#456     SK = DETAILS
PK = JOB#456     SK = REQUIREMENTS
```

For a small demo, we can load the job and opted-in candidate subsets and perform matching in Python. Later, indexes can replace broad scans as the dataset grows.

**No S3 required:** Store text-based questions, answers, scores, and compact job records directly in DynamoDB. Each item must remain within DynamoDB's 400 KB limit.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://aws.amazon.com\&sz=32)

Amazon Web Services



## **5. End-to-end workflow**

This is the main scenario we will demonstrate to judges.

1. **User selects a career goal**

   "I want to switch from Software Engineer to AI Engineer."

   The orchestrator saves the target role.
2. **Job Market Agent analyzes requirements**

   Retrieves relevant postings and identifies required skills with source references.
3. **Assessment Agent evaluates the user**

   Presents questions, grades responses, and saves evidence-backed results.
4. **Skill Coach creates a roadmap**

   Identifies missing requirements and generates a prioritized learning plan.
5. **User completes a learning milestone**

   The user takes a reassessment, and the Assessment Agent records the result.
6. **Marketplace recommends opportunities**

   Candidate-side matching uses the newly recorded skill evidence.
7. **Employer discovers a candidate**

   An employer sees the updated profile if the candidate has opted into marketplace discovery.

The key demonstration is the connection between learning and hiring:

**A completed assessment updates the candidate's evidence, which changes the information used by the marketplace.**

## **6. Agent execution and communication**

We will use the Strands **Agents-as-Tools** pattern rather than a complex agent network.

DynamoDBMarketplace AgentSkill CoachAssessment AgentJob Market AgentOrchestratorDynamoDBMarketplace AgentSkill CoachAssessment AgentJob Market AgentOrchestrator#chatgpt-mermaid-\_r_2ea\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_2ea\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_2ea\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_2ea\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_2ea\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_2ea\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_2ea\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_2ea\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_2ea\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_2ea\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_2ea\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_2ea\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2ea\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2ea\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_2ea\_ p{margin:0;}#chatgpt-mermaid-\_r_2ea\_ .actor{stroke:rgb(31, 78, 148);fill:rgb(19, 33, 54);stroke-width:1;}#chatgpt-mermaid-\_r_2ea\_ rect.actor.outer-path[data-look="neo"]{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2ea\_ rect.note[data-look="neo"]{stroke:rgb(58, 132, 63);fill:rgb(48, 48, 48);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2ea\_ text.actor>tspan{fill:rgb(237, 237, 237);stroke:none;}#chatgpt-mermaid-\_r_2ea\_ .actor-line{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2ea\_ .innerArc{stroke-width:1.5;stroke-dasharray:none;}#chatgpt-mermaid-\_r_2ea\_ .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2ea\_ .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2ea\_ [id$="-arrowhead"] path{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2ea\_ .sequenceNumber{fill:#505050;}#chatgpt-mermaid-\_r_2ea\_ [id$="-sequencenumber"]{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2ea\_ [id$="-crosshead"] path{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_2ea\_ .messageText{fill:rgb(237, 237, 237);stroke:none;}#chatgpt-mermaid-\_r_2ea\_ .labelBox{stroke:rgba(255, 255, 255, 0.15);fill:rgb(14, 14, 14);filter:none;}#chatgpt-mermaid-\_r_2ea\_ .labelText,#chatgpt-mermaid-\_r_2ea\_ .labelText>tspan{fill:rgb(237, 237, 237);stroke:none;}#chatgpt-mermaid-\_r_2ea\_ .loopText,#chatgpt-mermaid-\_r_2ea\_ .loopText>tspan{fill:rgb(237, 237, 237);stroke:none;}#chatgpt-mermaid-\_r_2ea\_ .sectionTitle,#chatgpt-mermaid-\_r_2ea\_ .sectionTitle>tspan{fill:rgb(237, 237, 237);stroke:none;}#chatgpt-mermaid-\_r_2ea\_ .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:rgba(255, 255, 255, 0.15);fill:rgba(255, 255, 255, 0.15);}#chatgpt-mermaid-\_r_2ea\_ .note{stroke:rgb(58, 132, 63);fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_2ea\_ .noteText,#chatgpt-mermaid-\_r_2ea\_ .noteText>tspan{fill:rgb(237, 237, 237);stroke:none;font-weight:normal;}#chatgpt-mermaid-\_r_2ea\_ .activation0{fill:rgb(48, 48, 48);stroke:hsl(0, 0%, 8.8235294118%);}#chatgpt-mermaid-\_r_2ea\_ .activation1{fill:rgb(48, 48, 48);stroke:hsl(0, 0%, 8.8235294118%);}#chatgpt-mermaid-\_r_2ea\_ .activation2{fill:rgb(48, 48, 48);stroke:hsl(0, 0%, 8.8235294118%);}#chatgpt-mermaid-\_r_2ea\_ .actorPopupMenu{position:absolute;}#chatgpt-mermaid-\_r_2ea\_ .actorPopupMenuPanel{position:absolute;fill:rgb(19, 33, 54);box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#chatgpt-mermaid-\_r_2ea\_ .actor-man circle,#chatgpt-mermaid-\_r_2ea\_ line{fill:rgb(19, 33, 54);stroke-width:2px;}#chatgpt-mermaid-\_r_2ea\_ g rect.rect{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_2ea\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_2ea\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_2ea\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_2ea\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_2ea\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2ea\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_2ea\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_2ea\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}UserI want to become an AI EngineerAnalyze relevant jobsRetrieve job recordsSkills and source evidencePrepare assessmentAssessment questionsPresent questionsSubmit answersGrade submissionSave assessment resultAssessment summaryCreate roadmapSave milestonesLearning planRecommend matching jobsRetrieve job and skill dataMatches and explanationsResults, roadmap and jobsUser

The orchestrator should call specialists only when relevant. Specialists read shared records from DynamoDB rather than passing large conversation histories to one another.

For the MVP, there is no need for agent-to-agent messaging queues, event buses, or asynchronous workflows.

## **7. Proposed project structure**

```

skillpilot/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── CandidateDashboard
│   │   │   ├── EmployerDashboard
│   │   │   └── Marketplace
│   │   └── components/
│   │       ├── Chat
│   │       ├── SkillProfile
│   │       └── Roadmap
│
├── backend/
│   ├── api.py
│   ├── main.py
│   ├── orchestrator.py
│   ├── agents/
│   │   ├── job_market.py
│   │   ├── assessment.py
│   │   ├── coach.py
│   │   └── marketplace.py
│   ├── tools/
│   │   ├── jobs.py
│   │   ├── assessments.py
│   │   └── matching.py
│   └── db.py
│
└── README.md

```

`main.py` provides the AgentCore entrypoint, while `api.py` provides the thin FastAPI interface. The application and its specialist agents are deployed together.

## **8. Frontend scope**

Build only three primary screens.

**Candidate Dashboard**

Current role, target role, assessed skills, skill gaps, learning roadmap, and SkillPilot chat.

**Candidate Marketplace**

Available jobs, supported requirements, remaining gaps, and links to applications.

**Employer Dashboard**

Create a job, view consenting candidates, and inspect relevant assessment evidence.

For the demo, use two server-controlled demo identities: one candidate and one employer. Do not expose AWS credentials in the browser. Access controls must be enforced by the backend, not by letting users choose arbitrary roles in a request.

Real login and production-grade employer authorization can follow after the hackathon.

## **9. Team responsibilities**

| Member                | Primary ownership                                     | Expected result                    |
| --------------------- | ----------------------------------------------------- | ---------------------------------- |
| **1. AI & AWS**       | Strands agents, orchestrator, Bedrock, AgentCore      | Working multi-agent backend        |
| **2. Backend & Data** | DynamoDB, job retrieval, assessment grading, matching | Reliable data and business logic   |
| **3. Frontend**       | React interface, dashboards, chat, marketplace        | Working end-to-end user experience |

All three members should collaborate on integration and the demo. Agree on API response formats early so frontend and backend development can proceed independently.

## **10. Implementation priorities**

**Priority 1 — Must work**

MVP

Orchestrator, Bedrock, one DynamoDB table, candidate profile, job requirements, one assessment, one roadmap, and candidate-to-job matching.

**Priority 2 — Strong demo**

Target

Employer job creation, opted-in candidate discovery, and a reassessment that updates matching results.

**Priority 3 — Only if time permits**

Optional

Automatic posting refresh, detailed analytics, multiple career tracks, application invitations, and additional assessment types.

For the assessment, start with fixed questions and deterministic grading. That gives us an auditable baseline while the agents handle question presentation, interpretation, explanations, and roadmap generation.

## **11. Architecture decisions we can defend to judges**

| Question                            | Answer                                                                                                                                                      |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Why multiple agents?                | Market research, assessment, coaching, and matching require different tools and specialized workflows.                                                      |
| Why use Strands?                    | It supports specialist agents as callable tools under one orchestrator.                                                                                     |
| Why Bedrock?                        | We need managed LLM inference for job interpretation and adaptive learning.                                                                                 |
| Why AgentCore?                      | It hosts our agent application and avoids managing the agent server infrastructure.                                                                         |
| Why only DynamoDB?                  | All MVP data is compact and structured. Object storage and search infrastructure are not yet needed.                                                        |
| Why not a vector database?          | Our small, normalized job/skill dataset can be queried and matched directly.                                                                                |
| Why not AWS Lambda for every agent? | The specialist agents already execute within the same AgentCore application. Separate services would add unnecessary orchestration and deployment overhead. |

### **Final scope**

# **5**

Agents total

# **1**

DynamoDB table

# **3**

Main UI screens

One deployed multi-agent application. One complete career-development and marketplace workflow.

**The key to winning is not showing the maximum number of agents or AWS services. It is demonstrating why each component exists and proving that the complete workflow actually works.**

For SkillPilot, the most compelling result is a candidate whose assessment-backed profile improves through learning, with those changes reflected in both the candidate and employer marketplaces.