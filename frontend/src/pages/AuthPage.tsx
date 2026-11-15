import { useState } from 'react'
import { ArrowRight, Check } from 'lucide-react'
import { api, type AccountSession, type Role } from '../api'
import {Brand} from '../components/Brand'
import { ThemeToggle } from '../components/ThemeToggle'

export function AuthPage({onSuccess}: {onSuccess: (session: AccountSession)=>Promise<void>}) {
  const [signup,setSignup]=useState(false)
  const [name,setName]=useState('')
  const [email,setEmail]=useState('')
  const [password,setPassword]=useState('')
  const [role,setRole]=useState<Role>('candidate')
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  function changeMode(){setSignup(!signup);setError('');setPassword('')}
  async function submit(e:React.FormEvent){
    e.preventDefault();setError('')
    setBusy(true)
    try{
      const body=signup?{name,email,password,role}:{email,password}
      const session=await api<AccountSession>(signup?'/auth/signup':'/auth/login','POST',body)
      setPassword('');await onSuccess(session)
    }catch(e){setError((e as Error).message)}finally{setBusy(false)}
  }
  return <div className="auth-layout"><section className="auth-story"><a href="#" className="brand" aria-label="CareerBuddy home"><Brand/></a><div className="auth-story-content"><span className="eyebrow">MAKE YOUR NEXT MOVE</span><h1>A clearer path<br/>to what’s next.</h1><p>Know where your skills stand. Build what’s missing. Find opportunities that fit.</p><div className="auth-proof">{['Understand the skills employers need','Turn learning into demonstrated progress','Connect with the right opportunities'].map(s=><p key={s}><Check size={17}/>{s}</p>)}</div></div><p className="auth-story-footer">Your ambition. A plan to get there.</p></section><section className="auth-main"><div className="auth-theme"><ThemeToggle/></div><div className="auth-card"><span className="eyebrow">{signup?'GET STARTED':'WELCOME BACK'}</span><h2>{signup?'Create your account':'Sign in to CareerBuddy'}</h2><p className="muted">{signup?'A few details, then a conversation about your goals.':'Continue your learning and career journey.'}</p><form className="auth-form" onSubmit={submit}>
      {signup&&<label>Full name<input required autoComplete="name" maxLength={80} value={name} onChange={e=>setName(e.target.value)}/></label>}<label>Email address<input required type="email" autoComplete="email" maxLength={254} value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Password<input required type="password" autoComplete={signup?'new-password':'current-password'} minLength={signup?8:1} maxLength={128} value={password} onChange={e=>setPassword(e.target.value)}/></label>{signup&&<><p className="muted text-sm">Use at least 8 characters.</p><label>I’m here to<select aria-label="Account purpose" value={role} onChange={e=>setRole(e.target.value as Role)}><option value="candidate">Develop my career</option><option value="employer">Find talent for my team</option></select></label></>}
      {error&&<p className="error" role="alert">{error}</p>}<button className="button primary wide" disabled={busy}>{busy?'Please wait…':signup?'Create account':'Sign in'}<ArrowRight size={16}/></button>
    </form><p className="auth-switch">{signup?'Already have an account?':'New to CareerBuddy?'} <button className="text-button" onClick={changeMode}>{signup?'Sign in':'Create an account'}</button></p></div><p className="auth-footer">Learning, skills, and opportunities. In one place.</p></section></div>
}
