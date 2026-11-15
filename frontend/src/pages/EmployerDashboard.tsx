import { useEffect, useState } from 'react'
import { Check, Plus, ShieldCheck, Users, X } from 'lucide-react'
import {GenerationLoader} from '../components/GenerationLoader'
import { api, skillLabel, TRACKS, LEVELS, type CareerLevel, type Job, type Candidate } from '../api'

export function EmployerDashboard({onError}: {onError: (text: string)=>void}) {
  const [jobs,setJobs]=useState<Job[]>([])
  const [selected,setSelected]=useState('')
  const [candidates,setCandidates]=useState<Candidate[]>([])
  const [showForm,setShowForm]=useState(false)
  const [busy,setBusy]=useState(false)
  const [loading,setLoading]=useState(true)
  const [title,setTitle]=useState('')
  const [company,setCompany]=useState('')
  const [description,setDescription]=useState('')
  const [level,setLevel]=useState<CareerLevel>('unspecified')
  async function loadJobs() {const data=await api<Job[]>('/employer/jobs');setJobs(data);setSelected(s=>s || data[0]?.id || '')}
  useEffect(()=>{void loadJobs().catch(e=>onError(e.message))},[])
  useEffect(()=>{if(!selected){setCandidates([]);setLoading(false);return}let active=true;setLoading(true);void api<Candidate[]>(`/employer/jobs/${selected}/candidates`).then(data=>{if(active)setCandidates(data)}).catch(e=>onError(e.message)).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[selected])
  async function create(e: React.FormEvent) {e.preventDefault();setBusy(true);try{const job=await api<Job>('/jobs','POST',{title,company,description,location:'Remote',required_skills:[],career_level:level});await loadJobs();setSelected(job.id);setShowForm(false)}catch(e){onError((e as Error).message)}finally{setBusy(false)}}
  const activeJob=jobs.find(j=>j.id===selected)
  return <div className="page-stack"><div className="page-title"><div><p className="eyebrow">HIRING WORKSPACE</p><h1>Find the skills your team needs.</h1><p className="muted">Review relevant skills and assessment evidence for each role.</p></div><button className="button primary" onClick={()=>setShowForm(!showForm)}>{showForm?<X size={16}/>:<Plus size={16}/>}Create a job</button></div>
    <div className="notice"><ShieldCheck size={20}/><span>Only opted-in candidates appear. Evidence comes from server-graded assessments. Matching is skill coverage, not a hiring recommendation.</span></div>
    {showForm && <form className="card section-card job-form" onSubmit={create}><h2>Create a job posting</h2><p className="muted text-sm">Paste the role description. CareerBuddy will identify and tag its requirements automatically.</p><div className="form-grid"><label>Job title<input required minLength={3} maxLength={120} value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Company<input required minLength={2} maxLength={100} value={company} onChange={e=>setCompany(e.target.value)}/></label></div><label>Career level<select aria-label="Posting career level" value={level} onChange={e=>setLevel(e.target.value as CareerLevel)}>{Object.entries(LEVELS).map(([v,label])=><option key={v} value={v}>{label}</option>)}</select></label><label>Description<textarea required minLength={20} maxLength={12000} value={description} onChange={e=>setDescription(e.target.value)}/></label>{busy&&<GenerationLoader task="jobs"/>}<button className="button primary" disabled={busy}>{busy?'Analyzing job requirements…':'Analyze and save posting'}</button></form>}
    <section className="card section-card"><div className="section-heading"><div><p className="eyebrow">YOUR OPEN ROLES</p><h2>Candidate discovery</h2></div><span className="pill">{jobs.length} postings</span></div><label className="job-select">Choose a job<select aria-label="Choose a job" value={selected} onChange={e=>setSelected(e.target.value)}>{jobs.map(j=><option key={j.id} value={j.id}>{j.title}</option>)}</select></label>{activeJob&&<div className="skill-tags">{activeJob.required_skills.map(s=><span key={s} className="pill">{skillLabel(s)}</span>)}</div>}{activeJob?.tagging_method==='llm'&&<p className="tag-provenance mt-3">Requirements identified from your posting by AI.</p>}<p className="muted text-sm">Candidates with at least one supported skill are shown below.</p>
      {loading ? <GenerationLoader task="matching" compact/> : candidates.length===0 ? <div className="empty"><Users size={30}/><h3>No consenting matches yet.</h3><p>Candidates appear after opting into discovery and demonstrating a relevant skill.</p></div> : <div className="candidate-list">{candidates.map(c=><article className="candidate-card" key={c.id}><div className="candidate-title"><div className="avatar">{c.name.split(' ').map(n=>n[0]).join('')}</div><div><h3>{c.name}</h3><p>{c.current_role} → {c.target_role}</p></div><span className="pill green">Opted in</span></div><div className="skill-tags"><span className="pill">{TRACKS[c.candidate_track]}</span><span className="pill">{c.supported_count} of {c.required_count} requirements</span>{c.supported.map(s=><span className="pill green" key={s}><Check size={12}/>{skillLabel(s)}</span>)}</div><p className="text-sm">{c.explanation}</p><details className="evidence-details"><summary>Inspect assessment evidence · {c.evidence.length} record{c.evidence.length===1?'':'s'}</summary>{c.evidence.map(e=><div className="evidence-row" key={e.assessment_id}><div><b>{skillLabel(e.skill)} · {e.score}%</b><p>{e.synthetic ? 'Seeded synthetic evidence' : 'Assessment-backed evidence'}</p><p>{e.scope}</p><code>Assessment {e.assessment_id.slice(0,12)} · {new Date(e.assessed_at).toLocaleDateString()}</code></div><ShieldCheck size={20}/></div>)}{c.synthetic && <p className="muted text-sm">Sample profile. Seeded assessment evidence is labeled above.</p>}</details></article>)}</div>}
    </section>
  </div>
}
