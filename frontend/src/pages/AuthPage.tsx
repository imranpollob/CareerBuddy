import { useState } from 'react'
import { ArrowRight, Check, Compass } from 'lucide-react'
import { api, LABELS, type AccountSession, type Role, type CandidateTrack } from '../api'
import { ThemeToggle } from '../components/ThemeToggle'

export function AuthPage({onSuccess}: {onSuccess: (session: AccountSession)=>Promise<void>}) {
  const [signup,setSignup]=useState(false)
  const [step,setStep]=useState(1)
  const [name,setName]=useState('')
  const [email,setEmail]=useState('')
  const [password,setPassword]=useState('')
  const [role,setRole]=useState<Role>('candidate')
  const [track,setTrack]=useState<CandidateTrack>('career_switcher')
  const [currentRole,setCurrentRole]=useState('')
  const [targetRole,setTargetRole]=useState('AI Engineer')
  const [skills,setSkills]=useState<string[]>([])
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  function changeMode(){setSignup(!signup);setStep(1);setError('');setPassword('')}
  async function submit(e:React.FormEvent){
    e.preventDefault();setError('')
    if(signup && step===1){setStep(2);return}
    setBusy(true)
    try{
      const body=signup?{name,email,password,role,current_role:role==='employer'?'Hiring manager':currentRole,target_role:role==='employer'?'Build an AI team':targetRole,candidate_track:track,claimed_skills:skills}:{email,password}
      const session=await api<AccountSession>(signup?'/auth/signup':'/auth/login','POST',body)
      setPassword('');await onSuccess(session)
    }catch(e){setError((e as Error).message)}finally{setBusy(false)}
  }
  return <div className="auth-layout"><section className="auth-story"><a href="#" className="brand" aria-label="SkillPilot home"><span className="brand-mark"><Compass size={24}/></span>skillpilot<span className="brand-dot">.</span></a><div className="auth-story-content"><span className="eyebrow">MAKE YOUR NEXT MOVE</span><h1>A clearer path<br/>to what’s next.</h1><p>Know where your skills stand. Build what’s missing. Find opportunities that fit.</p><div className="auth-proof">{['Understand the skills employers need','Turn learning into demonstrated progress','Connect with the right opportunities'].map(s=><p key={s}><Check size={17}/>{s}</p>)}</div></div><p className="auth-story-footer">Your ambition. A plan to get there.</p></section><section className="auth-main"><div className="auth-theme"><ThemeToggle/></div><div className="auth-card"><span className="eyebrow">{signup?'GET STARTED':'WELCOME BACK'}</span><h2>{signup?(step===1?'Create your account':'Make this workspace yours'):'Sign in to SkillPilot'}</h2><p className="muted">{signup?(step===1?'Start building your next opportunity.':'A few details help us guide your next steps.'):'Continue your learning and career journey.'}</p><form className="auth-form" onSubmit={submit}>
      {(!signup || step===1)?<>{signup&&<label>Full name<input required autoComplete="name" maxLength={80} value={name} onChange={e=>setName(e.target.value)}/></label>}<label>Email address<input required type="email" autoComplete="email" maxLength={254} value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Password<input required type="password" autoComplete={signup?'new-password':'current-password'} minLength={signup?12:1} maxLength={128} value={password} onChange={e=>setPassword(e.target.value)}/></label>{signup&&<p className="muted text-sm">Use at least 12 characters.</p>}</>:<><label>I’m here to<select aria-label="Account purpose" value={role} onChange={e=>setRole(e.target.value as Role)}><option value="candidate">Develop my career</option><option value="employer">Find talent for my team</option></select></label>{role==='candidate'&&<><label>My background<select aria-label="Career background" value={track} onChange={e=>setTrack(e.target.value as CandidateTrack)}><option value="career_switcher">Working professional exploring a new role</option><option value="student">Student or recent graduate</option><option value="experienced">Experienced AI practitioner</option></select></label><label>Current role or field of study<input required placeholder="e.g. Software Engineer or Computer Science Student" value={currentRole} maxLength={120} onChange={e=>setCurrentRole(e.target.value)}/></label><label>Target role<input required value={targetRole} maxLength={120} onChange={e=>setTargetRole(e.target.value)}/></label><fieldset><legend>Skills you already use <span className="muted">(optional)</span></legend><div className="checkboxes">{Object.entries(LABELS).map(([s,label])=><label key={s}><input type="checkbox" checked={skills.includes(s)} onChange={e=>setSkills(e.target.checked?[...skills,s]:skills.filter(x=>x!==s))}/>{label}</label>)}</div></fieldset><p className="muted text-sm">We currently focus on AI engineering careers. You control whether employers can discover your profile.</p></>}</>}
      {error&&<p className="error" role="alert">{error}</p>}<button className="button primary wide" disabled={busy}>{busy?'Please wait…':signup?(step===1?'Continue':'Create account'):'Sign in'}<ArrowRight size={16}/></button>{signup&&step===2&&<button className="text-button" type="button" onClick={()=>setStep(1)}>Back to account details</button>}
    </form><p className="auth-switch">{signup?'Already have an account?':'New to SkillPilot?'} <button className="text-button" onClick={changeMode}>{signup?'Sign in':'Create an account'}</button></p></div><p className="auth-footer">Learning, skills, and opportunities. In one place.</p></section></div>
}
