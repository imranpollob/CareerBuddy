import {useEffect,useState,useRef} from 'react'
import {ArrowRight,Compass,Send,Check} from 'lucide-react'
import {api,type OnboardingState,type Profile} from '../api'
import {ThemeToggle} from '../components/ThemeToggle'

export function OnboardingPage({name,onComplete,onSignOut}:{name:string;onComplete:(profile:Profile)=>Promise<void>;onSignOut:()=>void}){
  const [state,setState]=useState<OnboardingState|null>(null)
  const [answer,setAnswer]=useState('')
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const messagesRef=useRef<HTMLDivElement>(null)
  useEffect(()=>{if(messagesRef.current)messagesRef.current.scrollTop=messagesRef.current.scrollHeight},[state?.revision])
  async function load(){setError('');setBusy(true);try{setState(await api<OnboardingState>('/onboarding'))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
  useEffect(()=>{void load()},[])
  async function send(e:React.FormEvent){e.preventDefault();if(!state)return;setBusy(true);setError('');try{setState(await api<OnboardingState>('/onboarding/answer','POST',{answer,revision:state.revision}));setAnswer('')}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
  async function complete(){if(!state)return;setBusy(true);setError('');try{await onComplete(await api<Profile>('/onboarding/complete','POST',{revision:state.revision}))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
  return <div className="onboarding-shell"><header className="onboarding-header"><span className="brand"><span className="brand-mark"><Compass size={24}/></span>skillpilot.</span><div><ThemeToggle/><button className="text-button" onClick={onSignOut}>Sign out</button></div></header><main className="onboarding-main"><p className="eyebrow">LET’S GET TO KNOW YOU</p><h1>A plan built around you, {name.split(' ')[0]}.</h1><p className="muted">Tell SkillPilot about your experience. We’ll discover your skills together, then prepare a personalized assessment.</p>{state?.mode==='mock'&&<p className="pill">Offline preview · simulated interview</p>}
    {state&&<section className="card interview-card"><div ref={messagesRef} className="interview-messages" aria-live="polite">{state.messages.map((m,i)=><div className={`interview-message ${m.role==='user'?'from-user':''}`} key={i}><span>{m.role==='user'?'You':'SkillPilot'}</span><p>{m.content}</p></div>)}</div>{state.status==='review'?<div className="skill-review"><h2>Your discovered skills</h2><p className="muted text-sm">These are self-reported claims supported by your answers. An assessment will provide separate evidence.</p><div className="discovered-skills">{state.claims.map(c=><details key={c.skill}><summary><Check size={14}/>{c.label}</summary><p>“{c.evidence_excerpt}”</p></details>)}</div>{state.claims.length===0&&<p className="muted">No prior skills claimed yet. We can start with beginner fundamentals.</p>}<p className="text-sm">{state.current_role} → {state.target_role}</p><button className="button primary wide" disabled={busy} onClick={()=>void complete()}>{busy?'Preparing your personalized assessment…':'Confirm skills and create my assessment'}<ArrowRight size={16}/></button></div>:null}
      {state.status!=='completed'&&<form className="interview-answer" onSubmit={send}><label htmlFor="onboarding-answer">{state.status==='review'?'Add or correct anything before confirming':'Your answer'}</label><textarea id="onboarding-answer" required maxLength={3000} value={answer} onChange={e=>setAnswer(e.target.value)} placeholder="Describe your role, studies, projects, or tools in your own words…" disabled={busy}/><button className="button primary" disabled={busy||!answer.trim()}>{busy?'Thinking…':'Send answer'}<Send size={15}/></button></form>}
    </section>}{!state&&busy&&<p className="onboarding-loading" role="status">Preparing your first question…</p>}{error&&<div className="error" role="alert">{error}{!state&&<button className="text-button" onClick={()=>void load()}>Retry</button>}</div>}</main></div>
}
