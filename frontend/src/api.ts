export type Role = 'candidate' | 'employer'
export type CareerLevel = 'internship' | 'entry' | 'mid' | 'senior' | 'unspecified'
export type CandidateTrack = 'career_switcher' | 'student' | 'experienced' | 'employer' | 'unspecified'
export interface Profile {
  education_level?: string|null; years_experience?: number|null; expertise_level?: string|null
  id: string; role: Role; name: string; current_role: string; target_role: string
  claimed_skills: string[]; marketplace_opt_in: boolean; synthetic: boolean
  candidate_track: CandidateTrack
  goal_confirmed?:boolean
  onboarding_completed: boolean
  career_goal: CareerGoal
}
export type CareerGoal='unspecified'|'stay_relevant'|'find_job'|'switch_careers'
export const GOALS:Record<CareerGoal,string>={unspecified:'Choose your career purpose',stay_relevant:'Stay relevant in my current role',find_job:'Find a new job',switch_careers:'Switch careers'}
export interface AccountSession { profile: Profile; email: string; mode: 'mock' | 'bedrock' }
export type ProfileUpdate = Pick<Profile, 'name' | 'current_role' | 'target_role' | 'claimed_skills' | 'marketplace_opt_in'|'career_goal'>
export interface Evidence { skill: string; assessment_id: string; score: number; passed: boolean; assessed_at: string; scope: string; synthetic: boolean;mastery?:string;competency_ids?:string[];assessment_ids?:string[] }
export interface Question { id: string; prompt: string; choices: string[];format?:'knowledge'|'scenario' }
export interface Assessment {
  evaluation_id?:string|null;
  id: string; skill: string; status: 'pending' | 'completed'; created_at: string; questions: Question[]
  result?: {score: number; passed: boolean; scope: string; feedback: {question_id: string; correct: boolean; explanation: string}[]}
  kind: string; generation_model?: string; personalized_context?: string
  competency_id?:string;competency_title?:string;completed_at?:string;answers?:Record<string,number>|null
}
export interface Job {
  id: string; title: string; company: string; location: string; description: string; required_skills: string[]
  employer_id: string | null; source_url: string | null; source_name: string; retrieved_at: string; synthetic: boolean
  career_level: CareerLevel
  skill_tags: {skill:string;label:string;requirement:'required'|'preferred';evidence_excerpt:string}[]
  tagging_method: 'keywords'|'llm'|'mock'|'manual'; tagging_model?:string; tagged_at?:string
  role_family?: string|null
}
// Mirrors backend ROLE_FAMILY_LABELS (computer-science role areas).
export const ROLE_FAMILIES: Record<string,string> = {frontend:'Frontend',backend:'Backend',fullstack:'Full stack',software:'General software',
  mobile:'Mobile',ml_ai:'AI / ML',data_engineering:'Data engineering',data_science:'Data science & analytics',
  devops_sre:'DevOps / SRE / Infrastructure',security:'Security',qa:'Quality / testing'}
export interface Match { job: Job; supported: string[]; missing: string[]; supported_count: number; required_count: number; evidence: Evidence[]; explanation: string }
export interface Milestone { skill: string; title: string; status: string; job_count: number; estimated_minutes: number; lesson_completed: boolean }
export interface Roadmap { id: string; target_role: string; milestones: Milestone[]; note: string }
export interface Market { jobs: Job[]; posting_count: number; requirements: {skill: string; label: string; job_count: number}[]; note: string }
export interface Journey { title: string; description: string; portfolio_project: string; suggested_prompt: string; target_levels: string[] }
export interface Dashboard { profile: Profile; skills: Evidence[]; roadmap: Roadmap; assessments: Assessment[]; skill_catalog: Record<string, string>; market: Market; journey: Journey }
export interface Lesson { skill: string; title: string; content: string; exercise: string; completed: boolean;examples:string[];key_takeaways:string[];competency_id?:string }
export interface Candidate { id: string; name: string; current_role: string; target_role: string; synthetic: boolean; candidate_track: CandidateTrack; supported: string[]; missing: string[]; supported_count: number; required_count: number; evidence: Evidence[]; explanation: string }
export interface Health { ai_mode: 'mock' | 'bedrock'; repository: string; model_id: string; persistence: string }
export interface ChatResponse { message: string; mode: 'mock' | 'bedrock'; delegations: {specialist: string; tools: string[]; result: {summary: string; data: Record<string, unknown>}}[] }
export interface OnboardingState {question_number:number;total_questions:number;options:string[];answers:Record<string,string|number>;revision:number;status:'interview'|'review'|'completed';mode:'mock'|'bedrock';question:string;messages:{role:'assistant'|'user';content:string}[];claims:{skill:string;label:string;evidence_excerpt:string}[];current_role:string;target_role:string;candidate_track:CandidateTrack;career_goal:CareerGoal}
export interface Topic {id:string;skill:string;title:string;objective:string;format:'knowledge'|'scenario';status:'available'|'current'|'completed'|'practice_needed';lesson_completed:boolean;evidence:(Evidence&{id:string;title:string})|null}
export interface LearningPlan {market_role_covered?:boolean;role_job_ids?:string[];evaluation_id?:string|null;summary?:string|null;target_role:string;career_goal:CareerGoal;skills:{skill:string;label:string;job_count:number;rationale:string;expanded:boolean;topics:Topic[];mastery:string}[];next_topic:Topic|null;activity:{kind:'lesson'|'assessment';competency_id?:string;assessment_id?:string;skill:string;title:string}|null;completed_topics:number;total_topics:number;note:string}
export interface Passport {skills:Evidence[];competencies:(Evidence&{id:string;title:string})[];assessments:Assessment[];strengths:string[];next_steps:string[];note:string}
export interface Conversation {revision:number;messages:{role:'user'|'assistant';text:string;created_at:string;specialists:string[]}[]}

// Mirrors backend SKILLS so labels match before (or without) the catalog loading, e.g. for employers.
const BASE_LABELS: Record<string, string> = {python:'Python', sql:'SQL', llm:'LLM applications', rag:'RAG', pytorch:'PyTorch', aws:'AWS', evaluation:'AI evaluation',
  javascript:'JavaScript', typescript:'TypeScript', react:'React', fastapi:'FastAPI', docker:'Docker', git:'Git', machine_learning:'Machine learning',
  statistics:'Statistics', tensorflow:'TensorFlow', data_engineering:'Data engineering', nlp:'Natural language processing', kubernetes:'Kubernetes',
  java:'Java', cpp:'C++', postgresql:'PostgreSQL', prompt_engineering:'Prompt engineering', embeddings:'Embeddings', linux:'Linux'}
export const LABELS: Record<string, string> = {...BASE_LABELS}
export function setSkillCatalog(catalog:Record<string,string>={}){for(const key of Object.keys(LABELS))delete LABELS[key];Object.assign(LABELS,BASE_LABELS,catalog)}
export const LEVELS: Record<CareerLevel,string> = {internship:'Internship',entry:'Entry / graduate',mid:'Mid-level',senior:'Senior',unspecified:'Level not specified'}
export const TRACKS: Record<CandidateTrack,string> = {unspecified:'Not specified',career_switcher:'Career transition',student:'Student / graduate',experienced:'Experienced engineer',employer:'Employer'}
export function skillLabel(skill:string){return LABELS[skill] || skill.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase())}
// Career-stage fit (mirrors the backend marketplace ranking): early-career roles first for
// students and people with 0–1 years; internships last for people with 3+ years.
export function stageRank(job:Pick<Job,'career_level'>,profile:Pick<Profile,'candidate_track'|'years_experience'>){
  const years=profile.years_experience,early=profile.candidate_track==='student'||(years!=null&&years<=1)
  const isEarly=['internship','entry'].includes(job.career_level)
  if(early)return isEarly?0:1
  if(years!=null&&years>=3&&job.career_level==='internship')return 1
  return 0
}

export class ApiError extends Error { constructor(message: string, public status: number) { super(message) } }

export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {method, credentials:'include', headers: body === undefined ? {} : {'Content-Type':'application/json'}, body: body === undefined ? undefined : JSON.stringify(body)})
  const data = await response.json().catch(() => ({detail: 'The backend did not return a valid response.'}))
  if (!response.ok) {
    let message = typeof data.detail === 'string' ? data.detail : 'Please check the form fields and try again.'
    if (Array.isArray(data.detail)) {
      const errors = data.detail.map((issue: {loc?: (string | number)[]; msg?: string; type?: string; ctx?: {min_length?: number}}) => {
        const field = issue.loc?.filter(part => part !== 'body').join(' ').replaceAll('_',' ')
        if (field === 'password' && issue.type === 'too_short' && issue.ctx?.min_length) return `Password must be at least ${issue.ctx.min_length} characters.`
        if (field === 'email') return 'Enter a valid email address.'
        // Custom validators already phrase a full sentence; drop Pydantic's prefix.
        if (issue.msg?.startsWith('Value error, ')) return issue.msg.slice('Value error, '.length)
        return issue.msg ? `${field ? field.charAt(0).toUpperCase() + field.slice(1) + ': ' : ''}${issue.msg}` : ''
      }).filter(Boolean)
      if (errors.length) message = errors.join(' ')
    }
    throw new ApiError(message,response.status)
  }
  return data as T
}

export function evidenceScope(scope:string){return scope.replace(/^Generated four-question /i,'Four-question ').replace(/AI-authored questions are limited evidence/gi,'These questions provide limited evidence')}

export interface LearningEvaluation extends OnboardingState {id:string}
