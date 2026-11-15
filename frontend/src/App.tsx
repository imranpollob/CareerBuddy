import { useEffect, useState } from 'react'
import { ArrowRight, BriefcaseBusiness, Check, Compass, LayoutDashboard, LogOut, MessageCircle, Settings, Users, X } from 'lucide-react'
import { api, ApiError, LABELS, type Assessment as Attempt, type Dashboard, type Match, type AccountSession, type ProfileUpdate, type Lesson, type ChatResponse } from './api'
import { CandidateDashboard } from './pages/CandidateDashboard'
import { EmployerDashboard } from './pages/EmployerDashboard'
import { Marketplace } from './pages/Marketplace'
import { AuthPage } from './pages/AuthPage'
import { Chat } from './components/Chat'
import { Assessment } from './components/Assessment'
import { Modal } from './components/Modal'
import { ThemeToggle } from './components/ThemeToggle'
import { AssistantDrawer } from './components/AssistantDrawer'

export default function App(){
  const [account,setAccount]=useState<AccountSession|null>(null)
  const [view,setView]=useState<'dashboard'|'marketplace'>('dashboard')
  const [data,setData]=useState<Dashboard|null>(null)
  const [matches,setMatches]=useState<Match[]>([])
  const [attempt,setAttempt]=useState<Attempt|null>(null)
  const [lesson,setLesson]=useState<Lesson|null>(null)
  const [profile,setProfile]=useState<ProfileUpdate|null>(null)
  const [error,setError]=useState('')
  const [loading,setLoading]=useState(true)
  const [busy,setBusy]=useState(false)
  const [notice,setNotice]=useState('')
  const [chatOpen,setChatOpen]=useState(false)

  function handleError(e:unknown){
    setError(e instanceof Error?e.message:String(e))
    if(e instanceof ApiError&&e.status===401){setAccount(null);setData(null);setMatches([]);setChatOpen(false);setProfile(null);setLesson(null);setAttempt(null)}
  }
  async function refresh(){
    const [dashboard,jobMatches]=await Promise.all([api<Dashboard>('/dashboard'),api<Match[]>('/matches')])
    setData(dashboard);setMatches(jobMatches);setAccount(a=>a?{...a,profile:dashboard.profile}:a)
  }
  async function authenticated(session:AccountSession){
    setAccount(session);setLoading(true);setError('');setNotice('');setView('dashboard')
    try{if(session.profile.role==='candidate')await refresh()}catch(e){handleError(e)}finally{setLoading(false)}
  }
  useEffect(()=>{void api<AccountSession>('/session').then(authenticated).catch(e=>{if(!(e instanceof ApiError&&e.status===401))handleError(e);setLoading(false)})},[])
  async function signOut(){
    setBusy(true)
    try{await api('/auth/logout','POST');setAccount(null);setData(null);setMatches([]);setChatOpen(false);setProfile(null);setLesson(null);setAttempt(null);setNotice('');setError('')}
    catch(e){handleError(e)}finally{setBusy(false)}
  }
  async function assess(skill:string){setBusy(true);try{setAttempt(await api<Attempt>('/assessments','POST',{skill}))}catch(e){handleError(e)}finally{setBusy(false)}}
  async function openLesson(skill:string){setBusy(true);try{setLesson(await api<Lesson>(`/lessons/${skill}`))}catch(e){handleError(e)}finally{setBusy(false)}}
  async function completeLesson(){if(!lesson)return;setBusy(true);try{setAttempt(await api<Attempt>(`/lessons/${lesson.skill}/complete`,'POST'));setLesson(null);await refresh()}catch(e){handleError(e)}finally{setBusy(false)}}
  async function saveProfile(e:React.FormEvent){e.preventDefault();if(!profile)return;setBusy(true);try{await api('/profile','PATCH',profile);await refresh();setProfile(null);setNotice('Your profile has been updated.')}catch(e){handleError(e)}finally{setBusy(false)}}
  function editProfile(){if(!account)return;const {name,current_role,target_role,claimed_skills,marketplace_opt_in}=account.profile;setProfile({name,current_role,target_role,claimed_skills,marketplace_opt_in})}
  async function onChat(result:ChatResponse){
    if(account?.profile.role==='candidate'){
      await refresh();const delegated=result.delegations.find(d=>d.specialist==='assessment')
      if(delegated?.result.data.id){setChatOpen(false);setAttempt(await api<Attempt>(`/assessments/${delegated.result.data.id}`))}
    }
  }
  if(loading&&!account)return <div className="loading"><Compass size={32}/><p>Opening your workspace…</p></div>
  if(!account)return <>{error&&<div className="global-alert" role="alert">{error}</div>}<AuthPage onSuccess={authenticated}/></>
  const {profile:me}=account
  const employer=me.role==='employer'
  return <div className="app-shell product-shell"><aside className="sidebar"><a className="brand" href="#" onClick={e=>{e.preventDefault();setView('dashboard')}}><span className="brand-mark"><Compass size={24}/></span>skillpilot<span className="brand-dot">.</span></a><nav aria-label="Main navigation"><button className={view==='dashboard'?'active':''} onClick={()=>setView('dashboard')}>{employer?<Users size={18}/>:<LayoutDashboard size={18}/>} {employer?'Hiring workspace':'Overview'}</button>{!employer&&<button className={view==='marketplace'?'active':''} onClick={()=>setView('marketplace')}><BriefcaseBusiness size={18}/>Find jobs</button>}</nav><div className="account-menu"><div className="account-identity"><span className="avatar">{me.name.split(' ').map(n=>n[0]).slice(0,2).join('')}</span><div><b>{me.name}</b><small>{account.email}</small></div></div>{!employer&&<button className="account-action" onClick={editProfile}><Settings size={16}/>My profile</button>}<button className="account-action" disabled={busy} onClick={()=>void signOut()}><LogOut size={16}/>Sign out</button></div></aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumbs">{employer?'Talent workspace':view==='marketplace'?'Opportunities':'Career workspace'}</div><div className="topbar-actions"><ThemeToggle/><button className="button assistant-trigger" onClick={()=>setChatOpen(true)}><MessageCircle size={16}/>Ask SkillPilot</button><button className="mobile-signout icon-button" aria-label="Sign out" onClick={()=>void signOut()}><LogOut size={18}/></button></div></header>
      {error&&<div className="global-alert" role="alert"><span>{error}</span><button className="icon-button" aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}
      {notice&&<div className="success-alert" role="status"><Check size={16}/><span>{notice}</span><button className="icon-button" aria-label="Dismiss notification" onClick={()=>setNotice('')}><X size={16}/></button></div>}
      {loading?<div className="loading"><p>Loading your workspace…</p></div>:<div className="content-layout"><main>{employer?<EmployerDashboard key={me.id} onError={setError}/>:data?view==='marketplace'?<Marketplace matches={matches} student={me.candidate_track==='student'}/>:<CandidateDashboard data={data} onProfile={editProfile} onAssess={s=>void assess(s)} onLesson={s=>void openLesson(s)} onMarketplace={()=>setView('marketplace')} onResume={setAttempt}/>:<div className="empty"><p>We couldn’t load your workspace.</p><button className="button" onClick={()=>void authenticated(account)}>Try again</button></div>}</main></div>}
    </div>
    <AssistantDrawer open={chatOpen} onClose={()=>setChatOpen(false)}><Chat key={me.id} role={me.role} mode={account.mode} onResult={onChat}/></AssistantDrawer>
    {attempt&&<Assessment key={attempt.id} attempt={attempt} onClose={()=>setAttempt(null)} onSaved={refresh}/>}
    {lesson&&<Modal title={lesson.title} onClose={()=>setLesson(null)}><span className="pill">Practice, then reassess</span><p className="lesson-content">{lesson.content}</p><div className="exercise"><h3>Try it yourself</h3><p>{lesson.exercise}</p><p className="muted text-sm">Practice locally or on paper. The next assessment records evidence of understanding.</p></div><button className="button primary wide" disabled={busy} onClick={()=>void completeLesson()}>I’ve practiced · Start reassessment<ArrowRight size={16}/></button></Modal>}
    {profile&&<Modal title="My profile" onClose={()=>setProfile(null)}><form className="profile-form" onSubmit={saveProfile}><label>Name<input required maxLength={80} value={profile.name} onChange={e=>setProfile({...profile,name:e.target.value})}/></label><div className="form-grid"><label>Current role<input required maxLength={120} value={profile.current_role} onChange={e=>setProfile({...profile,current_role:e.target.value})}/></label><label>Career goal<input required maxLength={120} value={profile.target_role} onChange={e=>setProfile({...profile,target_role:e.target.value})}/></label></div><fieldset><legend>Self-reported skills</legend><div className="checkboxes">{Object.entries(LABELS).map(([s,label])=><label key={s}><input type="checkbox" checked={profile.claimed_skills.includes(s)} onChange={e=>setProfile({...profile,claimed_skills:e.target.checked?[...profile.claimed_skills,s]:profile.claimed_skills.filter(x=>x!==s)})}/>{label}</label>)}</div></fieldset><label className="opt-in"><input type="checkbox" checked={profile.marketplace_opt_in} onChange={e=>setProfile({...profile,marketplace_opt_in:e.target.checked})}/><span><b>Make my profile discoverable to employers</b><small>Share your name, role, and relevant assessment evidence. You can turn this off at any time.</small></span></label><p className="muted text-sm">Assessment results are updated only through graded submissions.</p><button className="button primary wide" disabled={busy}>{busy?'Saving…':'Save profile'}</button></form></Modal>}
  </div>
}
