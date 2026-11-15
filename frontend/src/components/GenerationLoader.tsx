import {useEffect,useState} from 'react'
export type GenerationTask='workspace'|'conversation'|'onboarding'|'assessment'|'roadmap'|'lesson'|'profile'|'jobs'|'matching'
const COPY:Record<GenerationTask,{title:string;notes:string[]}>={
 workspace:{title:'Opening your workspace',notes:['Picking up where you left off.','Your next chapter is warming up.']},
 conversation:{title:'Connecting the dots',notes:['A tiny career committee is in session.','Putting our thinking pixels on.','Looking for your next “aha!” moment.']},
 onboarding:{title:'Getting to know your experience',notes:['Every good plan starts with a good question.','Connecting your projects to your possibilities.','Your career story has our full attention.']},
 assessment:{title:'Creating your assessment',notes:['Warming up the brain gym.','Making the questions count. Not just counting questions.','A little challenge. A lot of possibility.']},
 roadmap:{title:'Building your learning path',notes:['Turning “someday” into a next step.','Untangling the spaghetti of possibilities.','Big ambitions, meet small achievable steps.']},
 lesson:{title:'Preparing your lesson',notes:['Finding the shortest route to “I get it.”','A fresh batch of “aha!” is on the way.','Adding examples. Holding the jargon.']},
 profile:{title:'Connecting your experience to a plan',notes:['Dusting off your hidden superpowers.','Connecting what you know to what comes next.','Your next chapter is taking shape.']},
 jobs:{title:'Identifying the skills in this role',notes:['Reading between the job-description lines.','Separating must-haves from nice-to-haves.','Giving this posting a skill check of its own.']},
 matching:{title:'Finding relevant evidence',notes:['Connecting skills with opportunities.','Looking for the useful overlaps.']},
}
export function GenerationLoader({task='conversation',compact=false}:{task?:GenerationTask;compact?:boolean}){
 const [note,setNote]=useState(0)
 useEffect(()=>{setNote(0);const timer=setInterval(()=>setNote(n=>n+1),4500);return()=>clearInterval(timer)},[task])
 const copy=COPY[task]
 return <div className={`generation-loader ${compact?'is-compact':''}`} role="status" aria-live="polite" aria-atomic="true"><div className="thinking-buddy" aria-hidden="true"><div className="buddy-orbit"><i/><i/><i/></div><div className="buddy-face"><span/><span/><b/></div><div className="buddy-shadow"/></div><div className="generation-copy"><strong>{copy.title}<span className="thinking-dots" aria-hidden="true"><i/><i/><i/></span></strong><p key={`${task}-${note}`} aria-hidden="true">{copy.notes[note%copy.notes.length]}</p></div></div>
}
