import {useEffect,useState,useRef} from 'react'
import {ArrowRight,BookOpen,BriefcaseBusiness,ChevronRight,House,LogOut,MessageCircle,ShieldCheck,UserRound,Users,X} from 'lucide-react'
import {api,ApiError,setSkillCatalog,type Assessment as Attempt,type Dashboard,type Match,type Job,type AccountSession,type ProfileUpdate,type Lesson,type ChatResponse,type LearningPlan,type Passport,type Topic} from './api'
import {HomePage,getNextAction,type HomeAction} from './pages/HomePage'
import {AuthPage} from './pages/AuthPage'
import {OnboardingPage} from './pages/OnboardingPage'
import {EmployerDashboard} from './pages/EmployerDashboard'
import {Marketplace} from './pages/Marketplace'
import {LearningPage} from './pages/LearningPage'
import {PassportPage} from './pages/PassportPage'
import {ProfilePage} from './pages/ProfilePage'
import {Chat} from './components/Chat'
import {Assessment} from './components/Assessment'
import {Modal} from './components/Modal'
import {Brand} from './components/Brand'
import {ThemeToggle} from './components/ThemeToggle'
import {GenerationLoader,type GenerationTask} from './components/GenerationLoader'
import {LearningEvaluation} from './components/LearningEvaluation'
import {Markdown} from './components/Markdown'
type View='home'|'chat'|'profile'|'learning'|'assessments'|'jobs'|'hiring'
const VIEWS:View[]=['home','chat','profile','learning','assessments','jobs','hiring']
// Hash routes (#/learning) give each page a URL so refresh, Back and links keep the page.
function viewFromHash():View|null{const v=location.hash.replace(/^#\/?/,'') as View;return VIEWS.includes(v)?v:null}
function allowedView(v:View,employer:boolean){return employer?v==='hiring'||v==='chat':v!=='hiring'}
const NAV=[{id:'home',label:'Home',icon:House},{id:'chat',label:'AI Chat',icon:MessageCircle},{id:'learning',label:'Learning',icon:BookOpen},{id:'assessments',label:'Assessments',icon:ShieldCheck},{id:'jobs',label:'Jobs',icon:BriefcaseBusiness}] as const
export default function App(){
 const identityVersion=useRef(0)
 const [account,setAccount]=useState<AccountSession|null>(null)
 const [view,setView]=useState<View>('home')
 const [data,setData]=useState<Dashboard|null>(null)
 const [matches,setMatches]=useState<Match[]>([])
 const [selectedJob,setSelectedJob]=useState<Job|null>(null)
 const [plan,setPlan]=useState<LearningPlan|null>(null)
 const [passport,setPassport]=useState<Passport|null>(null)
 const [attempt,setAttempt]=useState<Attempt|null>(null)
 const [evaluating,setEvaluating]=useState(false)
 const [lesson,setLesson]=useState<Lesson|null>(null)
 const [error,setError]=useState('')
 const [loading,setLoading]=useState(true)
 const [busy,setBusy]=useState(false)
 const [generation,setGeneration]=useState<GenerationTask|null>(null)
 const [chatVersion,setChatVersion]=useState(0)
 function clear(){setEvaluating(false);identityVersion.current++;setSkillCatalog();setAccount(null);setData(null);setMatches([]);setPlan(null);setPassport(null);setAttempt(null);setLesson(null);setSelectedJob(null)}
 function handleError(e:unknown){setError(e instanceof Error?e.message:String(e));if(e instanceof ApiError&&e.status===401)clear()}
 async function refresh(){const version=identityVersion.current;const [d,m,p,pass]=await Promise.all([api<Dashboard>('/dashboard'),api<Match[]>('/matches'),api<LearningPlan>('/learning'),api<Passport>('/passport')]);if(version!==identityVersion.current)return;setSkillCatalog(d.skill_catalog);setData(d);setMatches(m);setPlan(p);setPassport(pass);setAccount(a=>a?{...a,profile:d.profile}:a)}
 async function authenticated(session:AccountSession){identityVersion.current++;setData(null);setPlan(null);setPassport(null);setMatches([]);setAttempt(null);setLesson(null);setSelectedJob(null);setSkillCatalog();setAccount(session);setLoading(true);setError('');const employer=session.profile.role==='employer',requested=viewFromHash();setView(requested&&allowedView(requested,employer)?requested:employer?'hiring':'home');try{if(session.profile.role==='candidate'&&session.profile.onboarding_completed)await refresh()}catch(e){handleError(e)}finally{setLoading(false)}}
 useEffect(()=>{void api<AccountSession>('/session').then(authenticated).catch(e=>{if(!(e instanceof ApiError&&e.status===401))handleError(e);setLoading(false)})},[])
 // Keyed on the account id: refresh() replaces the account object and must not reset scroll.
 const accountId=account?.profile.id,employerAccount=account?.profile.role==='employer'
 useEffect(()=>{if(!accountId)return;const hash=`#/${view}`;if(location.hash!==hash){if(location.hash)history.pushState(null,'',hash);else history.replaceState(null,'',hash)}window.scrollTo(0,0);document.querySelector('.main-shell')?.scrollTo(0,0)},[view,accountId])
 useEffect(()=>{if(!accountId)return;const onPop=()=>{const v=viewFromHash();if(v&&allowedView(v,employerAccount))setView(v)};window.addEventListener('popstate',onPop);return()=>window.removeEventListener('popstate',onPop)},[accountId,employerAccount])
 async function signOut(){setBusy(true);try{await api('/auth/logout','POST');clear();setError('');history.replaceState(null,'',location.pathname)}catch(e){handleError(e)}finally{setBusy(false)}}
 async function assess(skill:string,competency_id?:string){setBusy(true);setGeneration('assessment');setError('');try{setAttempt(await api<Attempt>('/assessments','POST',{skill,competency_id}));await refresh()}catch(e){handleError(e)}finally{setBusy(false);setGeneration(null)}}
 async function nextAssessment(){setBusy(true);setGeneration('assessment');setError('');try{setAttempt(await api<Attempt>('/assessments/next','POST'));await refresh()}catch(e){handleError(e)}finally{setBusy(false);setGeneration(null)}}
 async function expand(skill:string){setBusy(true);setGeneration('roadmap');setError('');try{setPlan(await api<LearningPlan>(`/learning/${encodeURIComponent(skill)}/expand`,'POST'))}catch(e){handleError(e)}finally{setBusy(false);setGeneration(null)}}
 async function openTopic(topic:Pick<Topic,'id'>){setBusy(true);setGeneration('lesson');setError('');try{setLesson(await api<Lesson>(`/competencies/${encodeURIComponent(topic.id)}/lesson`));await refresh()}catch(e){handleError(e)}finally{setBusy(false);setGeneration(null)}}
 async function completeLesson(){if(!lesson)return;setBusy(true);setGeneration('assessment');setError('');try{const path=lesson.competency_id?`/competencies/${encodeURIComponent(lesson.competency_id)}/practice`:`/lessons/${lesson.skill}/complete`;setAttempt(await api<Attempt>(path,'POST'));setLesson(null);await refresh()}catch(e){handleError(e)}finally{setBusy(false);setGeneration(null)}}
 async function onChat(result:ChatResponse){if(account?.profile.role==='candidate'){await refresh();const a=result.delegations.find(d=>d.specialist==='assessment');if(a?.result.data.id)setAttempt(await api<Attempt>(`/assessments/${a.result.data.id}`))}}
 async function saveProfile(profile:ProfileUpdate){setBusy(true);setError('');try{await api('/profile','PATCH',profile);await refresh();return true}catch(e){handleError(e);return false}finally{setBusy(false)}}
 async function onboarded(profile:AccountSession['profile']){if(!account)return;setAccount({...account,profile});setView('home');setLoading(true);try{await refresh()}catch(e){handleError(e)}finally{setLoading(false)}}
 async function createRoadmap(){setEvaluating(true)}
 async function evaluated(next:LearningPlan){setPlan(next);await refresh();setEvaluating(false);setView('learning')}

 function navigate(next:View){setView(next);if(next==='jobs')setSelectedJob(null)}
 function homeAction(action:HomeAction){if(action.kind==='create'){void createRoadmap()}else if(action.kind==='resume')setAttempt(action.attempt);else if(action.kind==='lesson')void openTopic(action.topic);else if(action.kind==='assess')void assess(action.topic.skill,action.topic.id);else if(action.kind==='skill-check')void assess(action.skill);else if(action.kind==='build'){setView('learning');void expand(action.skill)}else navigate('jobs')}
 function viewJob(job:Job){setSelectedJob(job);setView('jobs')}

 if(loading&&!account)return <div className="loading"><GenerationLoader task="workspace"/></div>
 if(!account)return <>{error&&<div className="global-alert" role="alert">{error}</div>}<AuthPage onSuccess={authenticated}/></>
 if(account.profile.role==='candidate'&&!account.profile.onboarding_completed)return <OnboardingPage name={account.profile.name} onComplete={onboarded} onSignOut={()=>void signOut()}/>
 const me=account.profile,employer=me.role==='employer'
 return <div className="app-shell product-shell careerbuddy-shell linear-shell"><aside className="sidebar"><a className="brand" aria-label="CareerBuddy home" href="#" onClick={e=>{e.preventDefault();navigate(employer?'hiring':'home')}}><Brand/></a><nav aria-label="Main navigation">{employer?<><button className={view==='hiring'?'active':''} onClick={()=>setView('hiring')}><Users size={19}/><span>Hiring workspace</span></button><button className={view==='chat'?'active':''} onClick={()=>setView('chat')}><MessageCircle size={19}/><span>AI Chat</span></button></>:NAV.map(n=><button key={n.id} aria-current={view===n.id?'page':undefined} className={view===n.id?'active':''} onClick={()=>navigate(n.id)}><n.icon size={19}/><span>{n.label}</span></button>)}</nav><div className="account-menu"><div className="account-card"><div className="account-identity"><span className="avatar" aria-hidden="true">{me.name.trim().split(/\s+/).map(n=>n[0]).slice(0,2).join('').toUpperCase()||'U'}</span><div><b title={me.name}>{me.name}</b><small title={account.email}>{account.email}</small></div></div>{!employer&&<button className={`account-profile ${view==='profile'?'active':''}`} aria-current={view==='profile'?'page':undefined} onClick={()=>navigate('profile')}><UserRound size={16}/><span>My Profile</span><ChevronRight className="account-profile-chevron" size={14}/></button>}</div><div className="sidebar-controls">{!employer&&<button className={`icon-button mobile-profile ${view==='profile'?'active':''}`} aria-label="My Profile" title="My Profile" aria-current={view==='profile'?'page':undefined} onClick={()=>navigate('profile')}><UserRound size={17}/></button>}<ThemeToggle/><button className="account-action" aria-label="Sign out" disabled={busy} onClick={()=>void signOut()}><LogOut size={16}/><span>Sign out</span></button></div></div></aside><div className="main-shell">{error&&<div className="global-alert" role="alert"><span>{error}</span><button className="icon-button" aria-label="Dismiss error" onClick={()=>setError('')}><X size={16}/></button></div>}{generation&&!loading&&!lesson&&<div className="generation-dock"><GenerationLoader task={generation}/></div>}{loading?<div className="loading"><GenerationLoader task={generation||'workspace'}/></div>:<div className={`content-layout ${view==='chat'?'chat-layout':''}`}><main>{view==='chat'?<div className="chat-home"><Chat key={`${me.id}-${chatVersion}`} role={me.role} onResult={onChat}/></div>:employer?<EmployerDashboard key={me.id} onError={setError}/>:data&&plan&&passport?view==='home'?<HomePage data={data} plan={plan} passport={passport} matches={matches} busy={busy} onAction={homeAction} onLearning={()=>navigate('learning')} onPassport={()=>navigate('assessments')} onJobs={()=>navigate('jobs')} onJob={viewJob} onChat={()=>navigate('chat')} onResume={setAttempt}/>:view==='profile'?<ProfilePage key={me.id} data={data} busy={busy} onSave={saveProfile} onEvaluate={()=>void createRoadmap()} onPassport={()=>setView('assessments')}/>:view==='learning'?<LearningPage onCreate={()=>void createRoadmap()} plan={plan} busy={busy} onExpand={s=>void expand(s)} onLesson={t=>void openTopic(t)} onAssess={t=>void assess(t.skill,t.id)} onContinue={()=>homeAction(getNextAction(data,plan))}/>:view==='assessments'?<PassportPage passport={passport} data={data} plan={plan} busy={busy} onNext={()=>void nextAssessment()} onCreate={()=>void createRoadmap()} onResume={setAttempt} onAssess={s=>void assess(s)}/>:<Marketplace matches={matches} profile={me} initialJob={selectedJob} roleJobIds={plan.role_job_ids||[]} targetRole={plan.target_role}/>:<div className="empty"><p>We couldn’t load your workspace.</p><button className="button" onClick={()=>void authenticated(account)}>Try again</button></div>}</main></div>}</div>{evaluating&&<LearningEvaluation reevaluating={!!plan?.evaluation_id} onClose={()=>setEvaluating(false)} onSaved={evaluated}/>} {attempt&&<Assessment key={attempt.id} attempt={attempt} onClose={()=>setAttempt(null)} onSaved={refresh}/>} {lesson&&<Modal title={lesson.title} onClose={()=>setLesson(null)}><span className="pill">{lesson.competency_id?'Competency lesson':'Skill lesson'}</span><h3 className="lesson-section-title">Concept</h3><div className="lesson-content"><Markdown>{lesson.content}</Markdown></div>{lesson.examples?.length>0&&<><h3 className="lesson-section-title">Worked examples</h3>{lesson.examples.map((example,i)=><pre className="lesson-example" key={i}>{example}</pre>)}</>}{lesson.key_takeaways?.length>0&&<><h3 className="lesson-section-title">Key takeaways</h3><ul className="lesson-takeaways">{lesson.key_takeaways.map((s,i)=><li key={i}>{s}</li>)}</ul></>}<div className="exercise"><h3>Practice</h3><Markdown>{lesson.exercise}</Markdown><p className="muted text-sm">Practice locally or on paper. The next objective check records evidence of understanding.</p></div>{generation&&<GenerationLoader task={generation}/>}<button className="button primary wide" disabled={busy} onClick={()=>void completeLesson()}>I’ve practiced · Start assessment<ArrowRight size={16}/></button></Modal>}</div>
}
