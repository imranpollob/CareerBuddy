export type Role = 'candidate' | 'employer'
export type CareerLevel = 'internship' | 'entry' | 'mid' | 'senior' | 'unspecified'
export type CandidateTrack = 'career_switcher' | 'student' | 'experienced' | 'employer'
export interface Profile {
  id: string; role: Role; name: string; current_role: string; target_role: string
  claimed_skills: string[]; marketplace_opt_in: boolean; synthetic: boolean
  candidate_track: CandidateTrack
}
export interface AccountSession { profile: Profile; email: string; mode: 'mock' | 'bedrock' }
export type ProfileUpdate = Pick<Profile, 'name' | 'current_role' | 'target_role' | 'claimed_skills' | 'marketplace_opt_in'>
export interface Evidence { skill: string; assessment_id: string; score: number; passed: boolean; assessed_at: string; scope: string; synthetic: boolean }
export interface Question { id: string; prompt: string; choices: string[] }
export interface Assessment {
  id: string; skill: string; status: 'pending' | 'completed'; created_at: string; questions: Question[]
  result?: {score: number; passed: boolean; scope: string; feedback: {question_id: string; correct: boolean; explanation: string}[]}
}
export interface Job {
  id: string; title: string; company: string; location: string; description: string; required_skills: string[]
  employer_id: string | null; source_url: string | null; source_name: string; retrieved_at: string; synthetic: boolean
  career_level: CareerLevel
}
export interface Match { job: Job; supported: string[]; missing: string[]; supported_count: number; required_count: number; evidence: Evidence[]; explanation: string }
export interface Milestone { skill: string; title: string; status: string; job_count: number; estimated_minutes: number; lesson_completed: boolean }
export interface Roadmap { id: string; target_role: string; milestones: Milestone[]; note: string }
export interface Market { jobs: Job[]; posting_count: number; requirements: {skill: string; label: string; job_count: number}[]; note: string }
export interface Journey { title: string; description: string; portfolio_project: string; suggested_prompt: string; target_levels: string[] }
export interface Dashboard { profile: Profile; skills: Evidence[]; roadmap: Roadmap; assessments: Assessment[]; skill_catalog: Record<string, string>; market: Market; journey: Journey }
export interface Lesson { skill: string; title: string; content: string; exercise: string; completed: boolean }
export interface Candidate { id: string; name: string; current_role: string; target_role: string; synthetic: boolean; candidate_track: CandidateTrack; supported: string[]; missing: string[]; supported_count: number; required_count: number; evidence: Evidence[]; explanation: string }
export interface Health { ai_mode: 'mock' | 'bedrock'; repository: string; model_id: string; persistence: string }
export interface ChatResponse { message: string; mode: 'mock' | 'bedrock'; delegations: {specialist: string; tools: string[]; result: {summary: string; data: Record<string, unknown>}}[] }

export const LABELS: Record<string, string> = {python:'Python', sql:'SQL', llm:'LLM applications', rag:'RAG', pytorch:'PyTorch', aws:'AWS / Bedrock', evaluation:'AI evaluation'}
export const LEVELS: Record<CareerLevel,string> = {internship:'Internship',entry:'Entry / graduate',mid:'Mid-level',senior:'Senior',unspecified:'Level not specified'}
export const TRACKS: Record<CandidateTrack,string> = {career_switcher:'Career transition',student:'Student / graduate',experienced:'Experienced engineer',employer:'Employer'}

export class ApiError extends Error { constructor(message: string, public status: number) { super(message) } }

export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {method, credentials:'include', headers: body === undefined ? {} : {'Content-Type':'application/json'}, body: body === undefined ? undefined : JSON.stringify(body)})
  const data = await response.json().catch(() => ({detail: 'The backend did not return a valid response.'}))
  if (!response.ok) throw new ApiError(typeof data.detail === 'string' ? data.detail : 'Please check the form fields and try again.',response.status)
  return data as T
}
