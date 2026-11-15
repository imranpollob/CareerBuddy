import {useEffect,useState} from 'react'
import {ArrowRight} from 'lucide-react'
import {api,type OnboardingState,type Profile} from '../api'
import {Brand} from '../components/Brand'
import {ThemeToggle} from '../components/ThemeToggle'
import {GenerationLoader} from '../components/GenerationLoader'

export function OnboardingPage({name,onComplete,onSignOut}:{name:string;onComplete:(profile:Profile)=>Promise<void>;onSignOut:()=>void}){
 const [state,setState]=useState<OnboardingState|null>(null)
 const [answer,setAnswer]=useState('')
 const [busy,setBusy]=useState(false)
 const [error,setError]=useState('')
 async function load(){setError('');setBusy(true);try{setState(await api<OnboardingState>('/onboarding'))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 useEffect(()=>{void load()},[])
 async function send(e:React.FormEvent){e.preventDefault();if(!state)return;setBusy(true);setError('');try{setState(await api<OnboardingState>('/onboarding/answer','POST',{answer,revision:state.revision}));setAnswer('')}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function complete(){if(!state)return;setBusy(true);setError('');try{await onComplete(await api<Profile>('/onboarding/complete','POST',{revision:state.revision}))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <div className="onboarding-shell"><header className="onboarding-header"><span className="brand"><Brand/></span><div><ThemeToggle/><button className="text-button" onClick={onSignOut}>Sign out</button></div></header><main className="onboarding-main"><p className="eyebrow">LET’S GET TO KNOW YOU</p><h1>A plan built around you, {name.split(' ')[0]}.</h1><p className="muted">Four quick questions about your background. Your learning and assessments will use your own profile.</p>
 {state&&<section className="card interview-card">{state.status==='review'?<div className="skill-review"><h2>Your starting point</h2><dl>{Object.entries(state.answers).map(([key,value])=><div key={key} style={{marginBottom:16}}><dt className="muted">{{current_role:'Current role',education_level:'Education',years_experience:'Years of experience',expertise_level:'Self-reported expertise'}[key]||key}</dt><dd>{value}</dd></div>)}</dl><p className="muted">These answers personalize your starting point. Skills are verified separately through assessments.</p><button className="button primary wide" disabled={busy} onClick={()=>void complete()}>Create my workspace<ArrowRight size={16}/></button></div>:<form className="interview-answer" onSubmit={send}><p className="eyebrow" aria-live="polite">{state.question_number} of {state.total_questions}</p><progress aria-label="Onboarding progress" max={state.total_questions} value={state.question_number}/><h2><label htmlFor="onboarding-answer">{state.question}</label></h2>{state.options.length?<select id="onboarding-answer" required value={answer} onChange={e=>setAnswer(e.target.value)} disabled={busy}><option value="">Select an option</option>{state.options.map(o=><option key={o} value={o}>{o}</option>)}</select>:<input id="onboarding-answer" required maxLength={120} value={answer} onChange={e=>setAnswer(e.target.value)} placeholder="For example, software engineer or student" disabled={busy}/>}<button className="button primary" disabled={busy||!answer.trim()}>{state.question_number===4?'Review answers':'Continue'}<ArrowRight size={16}/></button></form>}{busy&&<GenerationLoader task="onboarding" compact/>}</section>}{!state&&busy&&<GenerationLoader task="onboarding"/>}{error&&<div className="error" role="alert">{error}{!state&&<button className="text-button" onClick={()=>void load()}>Retry</button>}</div>}</main></div>
}
