# **CareerBuddy — Features Discussed So Far**

**CareerBuddy** is an AI-powered career development platform that helps users identify required skills, learn continuously, demonstrate their abilities, and find relevant job opportunities.

**Core loop:** Career Goal → Skill Gap Analysis → Learning → Assessment → Skill Evidence → Job Matching

## **1. User Onboarding & Profile**

- Sign up / Login
- Choose career goal:
  - Stay relevant in current job
  - Find a new job
  - Switch careers
- Specify current role and dream job
- Add existing skills and experience
- AI-powered profile evaluation
- Identify strengths and skill gaps
- Track progress toward target role

## **2. AI Chat — Main Interface**

After login, users land on the **CareerBuddy Chat Screen**.

Suggested prompts:

- Evaluate my profile
- Show my next learning topic
- Take my next assessment
- Find matching jobs

**Features:**

- Conversational AI career assistant
- Context-aware recommendations
- Conversation history
- Multi-agent task delegation
- Personalized next-step suggestions
- Continue learning from previous progress

## **3. Learning Coach**

| Feature              | Description                                |
| -------------------- | ------------------------------------------ |
| Career Roadmap       | Personalized path toward the dream job     |
| Visual Learning Path | Interactive flowchart of skills and topics |
| Skill Breakdown      | Divide major skills into smaller topics    |
| Next Topic           | Recommend the next learning milestone      |
| AI Lesson Generator  | Generate lessons when users click topics   |
| Daily Learning       | Regular lessons based on learning goals    |
| Practice Exercises   | Exercises following lessons                |
| Adaptive Learning    | Adjust lessons based on assessment results |
| Progress Tracking    | Completed, current, and remaining topics   |
| Continue Learning    | Resume the last learning activity          |

**Lesson structure:**

Concept explanation → Examples → Key takeaways → Practice → Assessment

## **4. Assessments & Skill Mastery**

This is one of CareerBuddy's key differentiating features.

### **Assessment features**

- Skill-specific assessment pathways
- Break large skills into smaller competencies
- Progressive assessment milestones
- Multiple assessment formats:
  - Knowledge quizzes
  - Scenario-based challenges
  - Coding exercises
  - Explain-a-concept questions
  - Mini projects
  - Final skill challenges
- AI-generated questions and feedback
- Objective grading where possible
- Reassessment and retry options
- Strength and weakness analysis
- Assessment history

### **Skill mastery levels**

1. **Not Assessed** — No assessment evidence
2. **Foundational** — Basic concepts demonstrated
3. **Applied** — Practical tasks completed
4. **Demonstrated** — Integrated skill challenge completed

**Skill Passport:** A collection of assessment-backed skills showing competencies, results, dates, and supporting evidence.

Users may edit self-reported skills, but cannot directly change assessment-backed results.

## **5. Job Market Intelligence**

- Retrieve current job postings
- Identify skills employers require
- Analyze role-specific market demand
- Normalize related skill names
- Compare market requirements with personal skills
- Identify missing competencies
- Update recommendations as job-market data changes
- Show job sources and retrieval dates

Example: A user targeting AI engineering can see which skills appear in sampled relevant job postings and which of those skills they have demonstrated.

## **6. Two-Sided Job Marketplace**

**Candidate Side**

- Discover matching jobs
- View supported requirements
- Identify missing skills
- Understand job fit
- Follow learning recommendations
- Access job application links

**Employer Side**

- Create job postings
- Specify required skills
- Discover opted-in candidates
- Review assessment evidence
- See explainable matches
- Invite candidates to apply

Matching uses job-relevant skill evidence, not just resume keywords. Employers retain hiring decisions.

## **7. Multi-Agent AI System**

| Agent                      | Responsibility                            |
| -------------------------- | ----------------------------------------- |
| **Orchestrator**           | Main user conversation and delegation     |
| **Job Market Agent**       | Understand current job requirements       |
| **Skill Assessment Agent** | Evaluate skills and provide feedback      |
| **Learning Coach Agent**   | Generate roadmaps, lessons, and exercises |
| **Marketplace Agent**      | Match candidates with jobs and employers  |

All agents share persistent data, but have separate responsibilities and tools.

**Technology:** Amazon Bedrock + Strands Agents SDK + AgentCore Runtime + DynamoDB.

## **8. Application Navigation**

The candidate-facing sidebar contains:

**CareerBuddy**

AI Chat

Career assistant

My Profile

Career goal and skills

Learning

Roadmaps and lessons

Assessments

Skill mastery and evidence

Jobs

Career opportunities

Employers have a separate marketplace/dashboard view.

## **9. Hackathon MVP Priorities**

To keep the project manageable, these are the features I'd prioritize.

| Feature                               | Priority  |
| ------------------------------------- | --------- |
| AI chat with orchestrator             | Must have |
| User profile and dream job            | Must have |
| Job-market skill analysis             | Must have |
| Visual learning roadmap               | Must have |
| Click-to-generate AI lessons          | Must have |
| Competency-based assessments          | Must have |
| Assessment-backed skill progress      | Must have |
| Candidate job matching                | Must have |
| Basic employer marketplace            | Target    |
| Daily scheduled learning reminders    | Later     |
| Advanced coding assessments           | Later     |
| Full hiring and recruitment workflows | Later     |

## **10. The most important product feature**

I think CareerBuddy should revolve around **one continuously evolving Career Roadmap**.

Every major feature contributes to it:

- **Job Market Agent** determines what skills are needed.
- **Assessment Agent** determines what the user has demonstrated.
- **Learning Coach** decides what to learn next.
- **Marketplace Agent** identifies relevant opportunities.
- **Orchestrator** coordinates the experience.

This means users aren't simply taking random courses or quizzes. Every learning activity has a connection to their career goal.

**The central product promise: CareerBuddy helps you understand where you are, where you want to go, and what to do next—while showing evidence of your progress.**