import {ArrowRight,BookOpen,Check,ChevronRight,MessageCircle,ShieldCheck} from 'lucide-react'
import {GOALS,skillLabel,type Assessment,type Dashboard,type Job,type LearningPlan,type Match,type Passport,type Topic} from '../api'

type ActionDetails={title:string;description:string;label:string}
export type HomeAction=ActionDetails&(
 |{kind:'resume';attempt:Assessment}
 |{kind:'lesson';topic:Topic}
 |{kind:'assess';topic:Topic}
 |{kind:'build';skill:string}
 |{kind:'skill-check';skill:string}
 |{kind:'jobs'}
 |{kind:'create'}
)
export function getNextAction(data:Dashboard,plan:LearningPlan):HomeAction{
 const pending=data.assessments.filter(a=>a.status==='pending').sort((a,b)=>b.created_at.localeCompare(a.created_at))
 const attempt=pending.find(a=>a.id===plan.activity?.assessment_id)||pending[0]
 if(attempt)return {kind:'resume',attempt,title:`Finish your ${attempt.competency_title||skillLabel(attempt.skill)} assessment`,description:'Your questions are ready. Pick up where you left off and turn your understanding into evidence.',label:'Continue assessment'}
 const lastTopic=plan.skills.flatMap(s=>s.topics).find(t=>t.id===plan.activity?.competency_id)
 if(plan.activity?.kind==='lesson'&&lastTopic&&lastTopic.status!=='completed')return {kind:'lesson',topic:lastTopic,title:lastTopic.title,description:'Continue the lesson you opened, work through the examples, and practice before your next check.',label:'Continue lesson'}
 const topic=plan.next_topic
 if(topic){
  if(topic.lesson_completed&&topic.status!=='practice_needed')return {kind:'assess',topic,title:`Check your understanding of ${topic.title}`,description:'You have practiced this topic. A short objective check can record what you understand.',label:'Take the competency check'}
  return {kind:'lesson',topic,title:topic.title,description:topic.status==='practice_needed'?'Use your latest feedback to revisit the concepts, practice, and try again.':'A focused lesson and a practical exercise are your next steps toward this competency.',label:topic.status==='practice_needed'?'Review lesson':'Start lesson'}
 }
 if(!plan.skills.length)return {kind:'create',title:'Your workspace is ready',description:'Create a personal learning roadmap when you are ready to begin.',label:'Create my roadmap'}
 const missing=plan.skills.find(s=>s.mastery!=='foundational')
 if(missing?.expanded)return {kind:'skill-check',skill:missing.skill,title:`Refresh your ${missing.label} evidence`,description:'Your competency path is complete. Recheck your broader understanding to update your current skill evidence.',label:'Reassess skill'}
 if(missing)return {kind:'build',skill:missing.skill,title:`Build confidence in ${missing.label}`,description:'Open a three-step competency path connected to the skills in your target job sample.',label:'Build my learning path'}
 return {kind:'jobs',title:'Explore opportunities with your skills',description:'Review relevant roles, the requirements your evidence supports, and the gaps to work on next.',label:'Explore jobs'}
}
interface Props{
 data:Dashboard;plan:LearningPlan;passport:Passport;matches:Match[];busy:boolean
 onAction:(action:HomeAction)=>void;onLearning:()=>void;onPassport:()=>void;onJobs:()=>void;onJob:(job:Job)=>void;onChat:()=>void;onResume:(a:Assessment)=>void
}
export function HomePage({data,plan,passport,matches,busy,onAction,onLearning,onPassport,onJobs,onJob,onChat,onResume}:Props){
 const action=getNextAction(data,plan)
 const passed=passport.skills.filter(s=>s.passed)
 const latest=passport.assessments.filter(a=>a.status==='completed').sort((a,b)=>(b.completed_at||b.created_at).localeCompare(a.completed_at||a.created_at))[0]
 const gap=plan.skills.find(s=>s.mastery!=='foundational')
 const focus=plan.next_topic?.skill||gap?.skill
 const focusIndex=Math.max(0,plan.skills.findIndex(s=>s.skill===focus))
 const milestones=plan.skills.slice(focusIndex,focusIndex+3)
 const realJobs=matches.filter(m=>!m.job.synthetic&&!!m.job.source_url)
 const sample=realJobs.length?realJobs:matches
 const early=sample.filter(m=>['entry','internship'].includes(m.job.career_level))
 const opportunities=(data.profile.candidate_track==='student'&&early.length?early:sample).slice(0,3)
 if(!plan.skills.length&&!data.assessments.length&&!passport.skills.length)return <div className="page-stack home-page"><div className="home-heading"><div><h1>Welcome, {data.profile.name.split(' ')[0]}.</h1><p>Your career journey starts here.</p></div></div><section className="card home-next-step"><div><p className="eyebrow">GET STARTED</p><h2>Your workspace is ready</h2><p className="home-next-description">No roadmap, assessments, or verified skills yet. Create your personal roadmap using your background and career goal.</p></div><button className="button primary" disabled={busy} onClick={()=>onAction(action)}>Create my roadmap<ArrowRight size={16}/></button></section><div className="home-snapshots"><section className="card"><h2>Learning roadmap</h2><p>Your roadmap will appear here after you create it.</p></section><section className="card"><h2>Skill Passport</h2><p>No assessments or verified skills yet.</p></section></div></div>
 return <div className="page-stack home-page">
  <div className="home-heading"><div><h1>Good to see you, {data.profile.name.split(' ')[0]}.</h1><p>{GOALS[data.profile.career_goal]}<span aria-hidden="true"> · </span><span>{data.profile.current_role}<ArrowRight size={13}/>{data.profile.target_role}</span></p></div><div className="home-heading-actions"><button className="text-button" onClick={onChat}><MessageCircle size={16}/>Ask CareerBuddy</button></div></div>
  <section className="card home-next-step" aria-labelledby="home-next-heading"><div><p className="eyebrow">YOUR NEXT STEP</p><h2 id="home-next-heading">{action.title}</h2><p className="home-next-description">{action.description}</p></div><button className="button primary" disabled={busy} onClick={()=>onAction(action)}>{action.label}<ArrowRight size={16}/></button></section>
  <div className="home-snapshots">
   <section className="card home-roadmap" aria-labelledby="home-roadmap-heading"><div className="home-card-heading"><h2 id="home-roadmap-heading"><BookOpen size={18}/>Roadmap progress</h2><button className="text-button" onClick={onLearning}>View roadmap<ArrowRight size={14}/></button></div><p className="home-progress-copy"><strong>{plan.completed_topics}</strong> of {plan.total_topics} planned competencies passed</p><progress className="home-progress" aria-label="Roadmap competency progress" value={plan.completed_topics} max={Math.max(plan.total_topics,1)}/><ol className="home-milestones">{milestones.map((s,i)=>{const done=s.topics.filter(t=>t.status==='completed').length;return <li key={s.skill} className={i===0?'is-current':''}><span className="home-milestone-dot">{done===3?<Check size={12}/>:i+1}</span><div><b>{s.label}</b><small>{done===3?'Three competencies passed':s.expanded?`${done} of 3 competencies passed`:i===0?'Current focus · three competencies to explore':'Upcoming focus'}</small></div></li>})}</ol>{milestones.length===0&&<p className="home-empty-copy">Your learning path will appear here as role requirements become available.</p>}</section>
   <section className="card home-passport" aria-labelledby="home-passport-heading"><div className="home-card-heading"><h2 id="home-passport-heading"><ShieldCheck size={18}/>Skill Passport</h2><button className="text-button" onClick={onPassport}>View passport<ArrowRight size={14}/></button></div><p className="home-skill-count"><strong>{passed.length}</strong> foundational skill{passed.length===1?'':'s'}</p>{passed.length>0?<div className="skill-tags home-evidence-tags">{passed.slice(0,3).map(s=><span key={s.skill} className="pill green"><Check size={12}/>{skillLabel(s.skill)}</span>)}{passed.length>3&&<span className="pill">+{passed.length-3} more</span>}</div>:<p className="home-empty-copy">Self-reported experience stays separate. Your first passing skill check will start your passport.</p>}{latest?<button className="home-latest-result" onClick={()=>onResume(latest)}><span><small>Latest assessment · {new Date(latest.completed_at||latest.created_at).toLocaleDateString()}</small><b>{latest.competency_title||skillLabel(latest.skill)}</b></span><span className={`home-result-score ${latest.result?.passed?'is-passed':''}`}>{latest.result?.score}%<ChevronRight size={15}/></span></button>:<p className="home-first-check">No completed assessments yet.</p>}{gap&&<p className="home-next-gap">Next skill needing evidence: <b>{gap.label}</b></p>}</section>
  </div>
  <section className="card home-opportunities" aria-labelledby="home-jobs-heading"><div className="home-card-heading"><div><h2 id="home-jobs-heading">Relevant opportunities</h2><p>Compare requirements with your assessment evidence.</p></div><button className="text-button" onClick={onJobs}>Browse all jobs<ArrowRight size={14}/></button></div><div className="home-job-list">{opportunities.map(m=><article className="home-job" key={m.job.id}><div className="home-job-main"><h3>{m.job.title}</h3><p>{m.job.company}<span aria-hidden="true"> · </span>{m.job.location}</p><div className="home-job-evidence"><span className={m.supported_count?'has-support':''}>{m.supported_count} of {m.required_count} skill{m.required_count===1?'':'s'} supported</span><span className="home-job-gaps">{m.missing.length?`Evidence gaps: ${m.missing.slice(0,2).map(skillLabel).join(', ')}${m.missing.length>2?` +${m.missing.length-2} more`:''}`:'All tracked requirements supported'}</span></div></div><div className="home-job-action"><span className="home-source-label">{m.job.synthetic?'Sample posting':m.job.source_url?'Sourced posting':'Employer posting'}</span><button className="text-button" onClick={()=>onJob(m.job)}>View role<ArrowRight size={14}/></button></div></article>)}</div>{!opportunities.length&&<p className="home-empty-copy">No postings are available yet. Your skills and learning progress are saved.</p>}<p className="home-market-note">Saved job sample. Skill coverage is evidence of alignment, not a hiring or eligibility prediction.</p></section>
 </div>
}
