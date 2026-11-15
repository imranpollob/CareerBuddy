import { useEffect, useState } from 'react'
import { ArrowRight, BriefcaseBusiness, Check, ChevronDown, Compass, LayoutDashboard, ShieldCheck, Users, X } from 'lucide-react'
import { api, LABELS, type Assessment as Attempt, type Dashboard, type Match, type DemoIdentity, type ProfileUpdate, type Health, type Lesson, type ChatResponse } from './api'
import { CandidateDashboard } from './pages/CandidateDashboard'
import { EmployerDashboard } from './pages/EmployerDashboard'
import { Marketplace } from './pages/Marketplace'
import { Chat } from './components/Chat'
import { Assessment } from './components/Assessment'
import { Modal } from './components/Modal'
import { ThemeToggle } from './components/ThemeToggle'

export default function App() {
  const [identity,setIdentity]=useState<DemoIdentity>('candidate')
  const role = identity === 'employer' ? 'employer' : 'candidate'
  const [view,setView]=useState<'dashboard'|'marketplace'|'employer'>('dashboard')
  const [data,setData]=useState<Dashboard|null>(null)
  const [matches,setMatches]=useState<Match[]>([])
  const [health,setHealth]=useState<Health|null>(null)
  const [attempt,setAttempt]=useState<Attempt|null>(null)
  const [lesson,setLesson]=useState<Lesson|null>(null)
  const [profile,setProfile]=useState<ProfileUpdate|null>(null)
  const [error,setError]=useState('')
  const [loading,setLoading]=useState(true)
  const [busy,setBusy]=useState(false)
  const [sessionKey,setSessionKey]=useState(0)
  const [notice,setNotice]=useState('')

  const handleError=(e: unknown)=>setError(e instanceof Error?e.message:String(e))
  async function refresh() {const [dashboard,jobMatches]=await Promise.all([api<Dashboard>('/dashboard'),api<Match[]>('/matches')]);setData(dashboard);setMatches(jobMatches)}
  async function initialize() {
    setLoading(true);setError('')
    try {setHealth(await api<Health>('/health'));await api('/demo/candidate','POST');await refresh()}
    catch(e){handleError(e)}finally{setLoading(false)}
  }
  useEffect(()=>{void initialize()},[])
  async function switchIdentity(next: DemoIdentity) {
    if(next===identity || busy || loading)return
    setLoading(true);setError('');setNotice('');setAttempt(null);setLesson(null);setProfile(null)
    try {await api(`/demo/${next}`,'POST');setIdentity(next);setView(next==='employer'?'employer':'dashboard');setSessionKey(k=>k+1);if(next!=='employer')await refresh()}
    catch(e){handleError(e)}finally{setLoading(false)}
  }
  async function assess(skill: string) {setBusy(true);try{setAttempt(await api<Attempt>('/assessments','POST',{skill}))}catch(e){handleError(e)}finally{setBusy(false)}}
  async function openLesson(skill: string) {setBusy(true);try{setLesson(await api<Lesson>(`/lessons/${skill}`))}catch(e){handleError(e)}finally{setBusy(false)}}
  async function completeLesson() {if(!lesson)return;setBusy(true);try{setAttempt(await api<Attempt>(`/lessons/${lesson.skill}/complete`,'POST'));setLesson(null);await refresh()}catch(e){handleError(e)}finally{setBusy(false)}}
  async function saveProfile(e: React.FormEvent) {e.preventDefault();if(!profile)return;setBusy(true);try{await api('/profile','PATCH',profile);await refresh();setProfile(null);setNotice('Profile saved. Assessment evidence can only change through a graded submission.')}catch(e){handleError(e)}finally{setBusy(false)}}
  async function onChat(result: ChatResponse) {
    if(role==='candidate') {
      await refresh()
      const delegated=result.delegations.find(d=>d.specialist==='assessment')
      if(delegated?.result.data.id)setAttempt(await api<Attempt>(`/assessments/${delegated.result.data.id}`))
    }
  }
  const name=role==='candidate'?data?.profile.name || 'Alex Morgan':'Jordan Lee'
  return <div className="app-shell"><aside className="sidebar"><a className="brand" href="#" onClick={e=>{e.preventDefault();setView(role==='candidate'?'dashboard':'employer')}}><span className="brand-mark"><Compass size={24}/></span>skillpilot<span className="brand-dot">.</span></a><div className="workspace-label">YOUR WORKSPACE</div><nav aria-label="Main navigation">{role==='candidate'?<><button className={view==='dashboard'?'active':''} onClick={()=>setView('dashboard')}><LayoutDashboard size={18}/>My dashboard</button><button className={view==='marketplace'?'active':''} onClick={()=>setView('marketplace')}><BriefcaseBusiness size={18}/>Job marketplace<span className="nav-count">{matches.length}</span></button></>:<button className="active" onClick={()=>setView('employer')}><Users size={18}/>Employer dashboard</button>}</nav><div className="sidebar-note"><span className="small-compass"><Compass size={22}/></span><h3>A little progress.<br/>A lot of possibility.</h3><p>Skills you can demonstrate.<br/>A future you can shape.</p></div><div className="sidebar-bottom"><div className="demo-label"><span className="status-dot"/>BUILDERWARS · AWS HACKATHON</div><p>Local MVP · Demo identities</p><p className="text-xs">{health?.repository==='memory'?'Temporary memory · resets on restart':'Single-table DynamoDB'}</p></div></aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumbs">Workspace <span>/</span><b>{view==='dashboard'?'My dashboard':view==='marketplace'?'Job marketplace':'Employer dashboard'}</b></div><div className="topbar-actions"><ThemeToggle/><span className={`mode-badge ${health?.ai_mode==='bedrock'?'live':''}`}><span className="status-dot"/>{health?.ai_mode==='bedrock'?'Bedrock connected':'Mock mode'}</span><label className="role-switch"><span className="sr-only">Demo identity</span><select aria-label="Demo identity" value={identity} disabled={loading || busy} onChange={e=>void switchIdentity(e.target.value as DemoIdentity)}><option value="candidate">Software engineer demo</option><option value="student">Student demo</option><option value="employer">Employer demo</option></select><ChevronDown size={13}/></label><span className="avatar small-avatar" title={name}>{name.split(' ').map(n=>n[0]).join('')}</span></div></header>
      {error && <div className="global-alert" role="alert"><span>{error}</span><button className="icon-button" aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}
      {notice && <div className="success-alert" role="status"><Check size={16}/><span>{notice}</span><button className="icon-button" aria-label="Dismiss notification" onClick={()=>setNotice('')}><X size={16}/></button></div>}
      {loading ? <div className="loading"><Compass size={35}/><h2>Preparing your workspace…</h2><p>Loading your profile, evidence, and opportunities.</p></div> : !data && role==='candidate' ? <div className="empty"><h2>Let’s reconnect.</h2><p>Start the FastAPI backend, then try again.</p><button className="button primary" onClick={()=>void initialize()}>Retry connection</button></div> : <div className="content-layout"><main>{role==='candidate' && data ? view==='marketplace'?<Marketplace key={identity} matches={matches} student={identity==='student'}/>:<CandidateDashboard data={data} onProfile={()=>{const {name,current_role,target_role,claimed_skills,marketplace_opt_in}=data.profile;setProfile({name,current_role,target_role,claimed_skills,marketplace_opt_in})}} onAssess={s=>void assess(s)} onLesson={s=>void openLesson(s)} onMarketplace={()=>setView('marketplace')} onResume={setAttempt}/>:<EmployerDashboard key={sessionKey} onError={setError}/>}</main><Chat key={sessionKey} role={role} mode={health?.ai_mode || 'mock'} onResult={onChat}/></div>}
      <footer className="app-footer"><ShieldCheck size={13}/>Evidence informs opportunities. It doesn’t predict hiring decisions.<span>SkillPilot · Built with Strands + AWS</span></footer>
    </div>
    {attempt && <Assessment key={attempt.id} attempt={attempt} onClose={()=>setAttempt(null)} onSaved={refresh}/>}
    {lesson && <Modal title={lesson.title} onClose={()=>setLesson(null)}><span className="pill green">LEARN → PRACTICE → REASSESS</span><p className="lesson-content">{lesson.content}</p><div className="exercise"><h3>Try it yourself</h3><p>{lesson.exercise}</p><p className="muted text-sm">Practice locally or on paper. The next objective assessment records evidence of understanding.</p></div><button className="button primary wide" disabled={busy} onClick={()=>void completeLesson()}>I’ve practiced · Start reassessment<ArrowRight size={16}/></button><p className="muted text-sm mt-3">Reading a lesson never changes your assessed skills. Passing a fresh assessment does.</p></Modal>}
    {profile && <Modal title="Your career profile" onClose={()=>setProfile(null)}><form className="profile-form" onSubmit={saveProfile}><label>Name<input required maxLength={80} value={profile.name} onChange={e=>setProfile({...profile,name:e.target.value})}/></label><div className="form-grid"><label>Current role<input required maxLength={120} value={profile.current_role} onChange={e=>setProfile({...profile,current_role:e.target.value})}/></label><label>Career goal<input required maxLength={120} value={profile.target_role} onChange={e=>setProfile({...profile,target_role:e.target.value})}/></label></div><fieldset><legend>Self-reported skills</legend><div className="checkboxes">{Object.entries(LABELS).map(([s,label])=><label key={s}><input type="checkbox" checked={profile.claimed_skills.includes(s)} onChange={e=>setProfile({...profile,claimed_skills:e.target.checked?[...profile.claimed_skills,s]:profile.claimed_skills.filter(x=>x!==s)})}/>{label}</label>)}</div></fieldset><label className="opt-in"><input type="checkbox" checked={profile.marketplace_opt_in} onChange={e=>setProfile({...profile,marketplace_opt_in:e.target.checked})}/><span><b>Let demo employers discover my profile</b><small>Share your name, role, and relevant assessment evidence. You can opt out at any time.</small></span></label><div className="notice"><ShieldCheck size={18}/>Assessment results are protected. This form only changes your profile and self-reported skills.</div><button className="button primary wide" disabled={busy}>{busy?'Saving…':'Save profile'}</button></form></Modal>}
  </div>
}
