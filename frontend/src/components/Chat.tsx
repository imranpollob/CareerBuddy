import {useEffect,useRef,useState} from 'react'
import {ArrowUp,ChevronDown,SquarePen} from 'lucide-react'
import {Markdown} from './Markdown'
import {GenerationLoader} from './GenerationLoader'
import {api,type ChatResponse,type Role,type Conversation} from '../api'
interface Message {text:string;user?:boolean;trace?:ChatResponse['delegations'];specialists?:string[]}

// Profile evaluation is a structured flow on Home/Learning, not a chat prompt.
function suggestionsFor(role:Role,hasRoadmap:boolean){
  if(role==='employer')return ['Find candidates for my jobs','Which skills are hardest to find?','Analyze market requirements']
  return hasRoadmap
    ?['Show my next learning topic','Take my next assessment','Explain my skill gaps','Find matching jobs']
    :['How do I get started?','Which skills are employers asking for?','Find matching jobs']
}

export function Chat({role,hasRoadmap=false,onResult}:{role:Role;hasRoadmap?:boolean;onResult:(result:ChatResponse)=>Promise<void>}){
  const [messages,setMessages]=useState<Message[]>([])
  const [input,setInput]=useState('')
  const [busy,setBusy]=useState(false)
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [confirmingReset,setConfirmingReset]=useState(false)
  const scroll=useRef<HTMLDivElement>(null)
  const inputRef=useRef<HTMLInputElement>(null)
  async function load(){setLoading(true);setError('');try{const history=await api<Conversation>('/chat/history');setMessages(history.messages.map(m=>({text:m.text,user:m.role==='user',specialists:m.specialists})))}catch(e){setError((e as Error).message)}finally{setLoading(false)}}
  useEffect(()=>{void load()},[])
  useEffect(()=>{if(scroll.current)scroll.current.scrollTop=scroll.current.scrollHeight},[messages,busy,loading])
  async function send(text:string){
    if(!text.trim()||busy||loading)return
    setInput('');setError('');setBusy(true);setConfirmingReset(false)
    const previous=messages
    setMessages(m=>[...m,{text,user:true}])
    let result:ChatResponse
    try{result=await api<ChatResponse>('/chat','POST',{message:text})}
    catch(e){setMessages(previous);setInput(text);setError((e as Error).message);setBusy(false);return}
    setMessages(m=>[...m,{text:result.message,trace:result.delegations}])
    try{await onResult(result)}catch(e){setError(`Your reply is saved. The workspace could not refresh: ${(e as Error).message}`)}finally{setBusy(false)}
  }
  async function startNewChat(){
    setBusy(true);setError('')
    try{await api<Conversation>('/chat/clear','POST');setMessages([]);setInput('');setConfirmingReset(false);inputRef.current?.focus()}
    catch(e){setError((e as Error).message)}finally{setBusy(false)}
  }
  const suggestions=suggestionsFor(role,hasRoadmap)
  const hasMessages=messages.length>0
  return <section className="chat-panel card main-chat" aria-label="CareerBuddy chat">
    {hasMessages&&<div className="chat-toolbar">{confirmingReset
      ?<div className="chat-confirm" role="group" aria-label="Start a new chat"><span>Start a new chat? This conversation will be cleared. Your learning progress stays.</span><button className="button small primary" disabled={busy} onClick={()=>void startNewChat()}>Clear and start over</button><button className="button small" disabled={busy} onClick={()=>setConfirmingReset(false)}>Cancel</button></div>
      :<button className="chat-new" disabled={busy||loading} onClick={()=>setConfirmingReset(true)}><SquarePen size={15}/>New chat</button>}</div>}
    <div ref={scroll} className="chat-content" aria-live="polite">{loading?<GenerationLoader task="workspace" compact/>:!hasMessages&&<div className="chat-welcome"><h2>What would you like to work on?</h2><p>Ask about your skills, learning, or next opportunity.</p><div className="suggestions">{suggestions.map(s=><button key={s} onClick={()=>void send(s)}>{s}<span aria-hidden="true">↗</span></button>)}</div></div>}{messages.map((m,i)=><div key={i} className={`chat-message ${m.user?'user':''}`}><small>{m.user?'YOU':'CAREERBUDDY'}</small><Markdown>{m.text}</Markdown>{m.trace&&m.trace.length>0?<details className="trace"><summary>How this answer was prepared<ChevronDown size={12}/></summary>{m.trace.map((t,j)=><div key={j}><b>{t.specialist.replace('_',' ')}</b><span>{t.tools.join(', ')}</span><Markdown>{t.result.summary}</Markdown></div>)}</details>:null}</div>)}{busy&&!confirmingReset&&<GenerationLoader task="conversation"/>}{error&&<div className="error" role="alert">{error}{loading===false&&messages.length===0&&<button className="text-button" onClick={()=>void load()}>Reload history</button>}</div>}</div>
    <form className="chat-input" onSubmit={e=>{e.preventDefault();void send(input)}}><input ref={inputRef} aria-label="Message CareerBuddy" value={input} onChange={e=>setInput(e.target.value)} placeholder="Message CareerBuddy…" maxLength={3000}/><button disabled={busy||loading||!input.trim()} aria-label="Send message"><ArrowUp size={19}/></button></form>
    {/* Follow-up suggestions stay available under the input; hidden while typing. */}
    {hasMessages&&!input.trim()&&<div className="chat-chips" aria-label="Suggested prompts">{suggestions.map(s=><button key={s} type="button" disabled={busy||loading} onClick={()=>void send(s)}>{s}</button>)}</div>}
  </section>
}
