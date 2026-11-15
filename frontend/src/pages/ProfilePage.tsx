import {useState} from 'react'
import {ArrowRight,ShieldCheck} from 'lucide-react'
import {GOALS,skillLabel,type Dashboard,type ProfileUpdate,type CareerGoal} from '../api'
export function ProfilePage({data,busy,onSave,onEvaluate,onPassport}:{data:Dashboard;busy:boolean;onSave:(p:ProfileUpdate)=>Promise<boolean>;onEvaluate:()=>void;onPassport:()=>void}){
 const p=data.profile
 const [form,setFormState]=useState<ProfileUpdate>({name:p.name,current_role:p.current_role,target_role:p.target_role,career_goal:p.career_goal,claimed_skills:p.claimed_skills,marketplace_opt_in:p.marketplace_opt_in})
 const [extra,setExtra]=useState('')
 const [saved,setSaved]=useState(false)
 // Any edit makes an earlier "saved" confirmation stale.
 function setForm(next:ProfileUpdate){setFormState(next);setSaved(false)}
 function addSkill(){const skill=extra.trim().toLowerCase().replace(/\s+/g,'_');if(!skill||form.claimed_skills.length>=20)return;setForm({...form,claimed_skills:[...new Set([...form.claimed_skills,skill])]});setExtra('')}
 async function submit(e:React.FormEvent){e.preventDefault();setSaved(false);if(await onSave(form))setSaved(true)}
 const background=[['Education',p.education_level],['Years of experience',p.years_experience],['Self-reported expertise',p.expertise_level]].filter(([,v])=>v!==null&&v!==undefined&&v!=='')
 return <div className="page-stack"><div className="page-title"><div><h1>A career plan that fits you.</h1><p className="muted">Your experience shapes the guidance. Assessments provide separate evidence.</p></div><button className="button" onClick={onEvaluate}>{p.goal_confirmed?'Re-evaluate profile':'Evaluate my profile'}<ArrowRight size={15}/></button></div>
  <form className="card section-card profile-page-form" onSubmit={e=>void submit(e)}><h2>Career direction</h2><div className="form-grid">
   <label>Full name<input required maxLength={80} value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label>
   <label>Career purpose<select aria-label="Career purpose" value={form.career_goal} onChange={e=>setForm({...form,career_goal:e.target.value as CareerGoal})}>{Object.entries(GOALS).map(([value,label])=><option key={value} value={value} disabled={value==='unspecified'}>{label}</option>)}</select></label>
   <label>Current role<input required maxLength={120} value={form.current_role} onChange={e=>setForm({...form,current_role:e.target.value})}/></label>
   <label>Target role<input required maxLength={120} value={form.target_role} onChange={e=>setForm({...form,target_role:e.target.value})}/></label>
  </div>
  {background.length>0&&<div><h2>Background</h2><p className="muted text-sm">From your onboarding answers.</p><dl className="profile-background">{background.map(([label,value])=><div key={label as string}><dt className="muted text-sm">{label}</dt><dd>{value}</dd></div>)}</dl></div>}
  <div><h2>Self-reported skills</h2><p className="muted text-sm">Update your experience without changing assessment-backed results.</p><div className="profile-claims">{form.claimed_skills.map(s=><button type="button" className="pill" key={s} onClick={()=>setForm({...form,claimed_skills:form.claimed_skills.filter(x=>x!==s)})}>{skillLabel(s)} <span aria-label={`Remove ${skillLabel(s)}`}>×</span></button>)}</div>
   <div className="add-skill"><input aria-label="Add a self-reported skill" placeholder="Add a skill, e.g. TypeScript" value={extra} maxLength={50} onChange={e=>setExtra(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'){e.preventDefault();addSkill()}}}/><button type="button" className="button" disabled={!extra.trim()||form.claimed_skills.length>=20} onClick={addSkill}>Add skill</button></div></div>
  <label className="opt-in"><input type="checkbox" checked={form.marketplace_opt_in} onChange={e=>setForm({...form,marketplace_opt_in:e.target.checked})}/><span><b>Make my profile discoverable to employers</b><small>Share name, role, and relevant assessment evidence. Turn this off at any time.</small></span></label>
  {saved&&<p className="saved-message" role="status">Your profile has been saved.</p>}<button className="button primary" disabled={busy}>{busy?'Saving…':'Save profile'}</button></form>
  <section className="card section-card passport-callout"><ShieldCheck size={26}/><div><h2>Your evidence has its own home.</h2><p>Review competencies, results, dates, and feedback in your Skill Passport.</p></div><button className="text-button" onClick={onPassport}>View Skill Passport<ArrowRight size={14}/></button></section></div>
}
