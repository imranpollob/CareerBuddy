import { useState } from 'react'
import { ArrowUpRight, BriefcaseBusiness, Check, MapPin, Search } from 'lucide-react'
import { type Match, type Job, type CareerLevel, type Profile, skillLabel, stageRank, LEVELS, ROLE_FAMILIES } from '../api'
import { Modal } from '../components/Modal'

const PREVIEW_CHARS=1400

export function Marketplace({matches,profile,initialJob=null,roleJobIds=[],targetRole=''}: {matches: Match[];profile:Pick<Profile,'candidate_track'|'years_experience'>;initialJob?:Job|null;roleJobIds?:string[];targetRole?:string}) {
  const [query,setQuery]=useState('')
  const [selected,setSelected]=useState<Job|null>(initialJob)
  const [level,setLevel]=useState<CareerLevel|'all'|'early'>('all')
  const [area,setArea]=useState('all')
  const roleIds=new Set(roleJobIds)
  const q=query.trim().toLowerCase()
  const areas=Object.entries(ROLE_FAMILIES).filter(([key])=>matches.some(m=>m.job.role_family===key))
  const filtered=matches.filter(m=>(level==='all' || (level==='early'?['entry','internship'].includes(m.job.career_level):m.job.career_level===level))
    && (area==='all' || m.job.role_family===area)
    && `${m.job.title} ${m.job.company} ${m.job.required_skills.map(s=>`${s} ${skillLabel(s)}`).join(' ')}`.toLowerCase().includes(q))
  // Roles that fit the target role first; the backend already orders by evidence coverage.
  const ordered=[...filtered].sort((a,b)=>Number(roleIds.has(b.job.id))-Number(roleIds.has(a.job.id))||stageRank(a.job,profile)-stageRank(b.job,profile))
  const selectedMatch=selected?matches.find(m=>m.job.id===selected.id):undefined
  const supported=new Set(selectedMatch?.supported||[])
  return <div className="page-stack"><div className="page-title"><div><p className="eyebrow">OPPORTUNITIES</p><h1>Find your next opportunity.</h1><p className="muted">Compare each posting’s requirements with your assessment evidence.{roleIds.size>0&&targetRole?` Roles matching ${targetRole} are listed first.`:''}</p></div></div>
    <div className="notice"><BriefcaseBusiness size={20}/><span>Coverage counts only skills you have passed assessments for; self-reported skills don’t count. Read the original posting for full requirements.</span></div>
    <div className="job-filters"><label className="level-filter">Role area<select aria-label="Role area" value={area} onChange={e=>setArea(e.target.value)}><option value="all">All role areas</option>{areas.map(([value,label])=><option value={value} key={value}>{label}</option>)}</select></label>
    <label className="level-filter">Career stage<select aria-label="Career stage" value={level} onChange={e=>setLevel(e.target.value as typeof level)}><option value="all">All career stages</option><option value="early">Internships + entry / graduate</option>{Object.entries(LEVELS).map(([value,label])=><option value={value} key={value}>{label}</option>)}</select></label></div>
    <div className="market-toolbar"><label className="search"><Search size={17}/><input aria-label="Search jobs" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search roles, companies, skills…"/></label><span className="muted text-sm">{ordered.length} opportunit{ordered.length===1?'y':'ies'}</span></div>
    <div className="job-grid">{ordered.map(m=><article className="card job-card" key={m.job.id}><div className="job-top"><span className="company-icon">{m.job.company.slice(0,1)}</span>{roleIds.has(m.job.id)?<span className="pill green">Matches your target role</span>:m.job.synthetic?<span className="pill">Sample posting</span>:!m.job.source_url&&<span className="pill">Employer posting</span>}</div><p className="company-name">{m.job.company}</p><h2>{m.job.title}</h2><p className="job-location"><MapPin size={13}/>{m.job.location}</p>{m.job.career_level!=='unspecified'&&<div className="skill-tags mt-3"><span className="pill">{LEVELS[m.job.career_level]}</span></div>}<div className="coverage-label"><b>{m.supported_count} of {m.required_count}</b><span>skills supported by evidence</span></div><div className="coverage-track"><div style={{width:`${100*m.supported_count/Math.max(m.required_count,1)}%`}}/></div><div className="skill-tags">{m.supported.map(s=><span className="pill green" key={s}><Check size={12}/>{skillLabel(s)}</span>)}{m.missing.map(s=><span className="pill" key={s}>{skillLabel(s)}</span>)}</div><div className="job-bottom"><button className="text-button" onClick={()=>setSelected(m.job)}>View details<ArrowUpRight size={14}/></button>{m.job.source_url && <a href={m.job.source_url} target="_blank" rel="noreferrer" className="source-link">Original posting<ArrowUpRight size={13}/></a>}</div></article>)}</div>
    {ordered.length===0 && <div className="card empty"><Search size={30}/><h3>No roles match these filters.</h3><p>Try another skill, company, or career stage.</p>{(query||level!=='all'||area!=='all')&&<button className="button" onClick={()=>{setQuery('');setLevel('all');setArea('all')}}>Clear filters</button>}</div>}
    <p className="muted text-sm">Career stage comes from explicit title labels, not inferred eligibility. Public postings are a saved snapshot{matches[0]?` retrieved ${new Date(matches[0].job.retrieved_at).toLocaleDateString()}`:''} and may no longer be open.</p>
    {selected && <Modal title={selected.title} onClose={()=>setSelected(null)}><p className="eyebrow">{selected.company}</p><div className="notice">{selected.synthetic?'Sample posting':selected.source_name.replace(' (AI-identified requirements)','')} · retrieved {new Date(selected.retrieved_at).toLocaleDateString()}</div><section className="job-tag-evidence"><h3>Identified skill requirements</h3>{selected.skill_tags?.map(t=><details key={t.skill}><summary>{supported.has(t.skill)&&<Check size={13}/>}{skillLabel(t.skill)}<span className={`pill ${supported.has(t.skill)?'green':''}`}>{supported.has(t.skill)?'You have evidence':t.requirement}</span></summary><p>“{t.evidence_excerpt}”</p></details>)}</section><p className="posting-description">{(()=>{const text=selected.synthetic?selected.description.replace(/^Synthetic demonstration role\.\s*/,'Sample role. '):selected.description;return selected.source_url&&text.length>PREVIEW_CHARS?`${text.slice(0,PREVIEW_CHARS).trimEnd()}…`:text})()}</p>{selected.source_url && <a className="button primary" href={selected.source_url} target="_blank" rel="noreferrer">Read full posting<ArrowUpRight size={15}/></a>}</Modal>}
  </div>
}
