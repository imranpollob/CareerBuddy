import {useEffect,useRef,useState} from 'react'
import {ArrowUp,ChevronDown} from 'lucide-react'
import {Markdown} from './Markdown'
import {GenerationLoader} from './GenerationLoader'
import {api,type ChatResponse,type Role,type Conversation} from '../api'
interface Message {text:string;user?:boolean;trace?:ChatResponse['delegations'];specialists?:string[]}
export function Chat({role,onResult}:{role:Role;onResult:(result:ChatResponse)=>Promise<void>}){
  const [messages,setMessages]=useState<Message[]>([])
  const [input,setInput]=useState('')
  const [busy,setBusy]=useState(false)
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const scroll=useRef<HTMLDivElement>(null)
  async function load(){setLoading(true);setError('');try{const history=await api<Conversation>('/chat/history');setMessages(history.messages.map(m=>({text:m.text,user:m.role==='user',specialists:m.specialists})))}catch(e){setError((e as Error).message)}finally{setLoading(false)}}
  useEffect(()=>{void load()},[])
  useEffect(()=>{if(scroll.current)scroll.current.scrollTop=scroll.current.scrollHeight},[messages,busy,loading])
  async function send(text:string){
    if(!text.trim()||busy||loading)return
    setInput('');setError('');setBusy(true)
    const previous=messages
    setMessages(m=>[...m,{text,user:true}])
    let result:ChatResponse
    try{result=await api<ChatResponse>('/chat','POST',{message:text})}
    catch(e){setMessages(previous);setInput(text);setError((e as Error).message);setBusy(false);return}
    setMessages(m=>[...m,{text:result.message,trace:result.delegations}])
    try{await onResult(result)}catch(e){setError(`Your reply is saved. The workspace could not refresh: ${(e as Error).message}`)}finally{setBusy(false)}
  }
  // Profile evaluation is a structured flow on Home/Learning, not a chat prompt.
  const suggestions=role==='candidate'?['Show my next learning topic','Take my next assessment','Explain my skill gaps','Find matching jobs']:['Find candidates for my jobs','Analyze market requirements']
  return <section className="chat-panel card main-chat" aria-label="CareerBuddy chat"><div ref={scroll} className="chat-content" aria-live="polite">{loading?<GenerationLoader task="workspace" compact/>:messages.length===0&&<div className="chat-welcome"><h2>What would you like to work on?</h2><p>Ask about your skills, learning, or next opportunity.</p><div className="suggestions">{suggestions.map(s=><button key={s} onClick={()=>void send(s)}>{s}<span aria-hidden="true">↗</span></button>)}</div></div>}{messages.map((m,i)=><div key={i} className={`chat-message ${m.user?'user':''}`}><small>{m.user?'YOU':'CAREERBUDDY'}</small><Markdown>{m.text}</Markdown>{m.trace&&m.trace.length>0?<details className="trace"><summary>How this answer was prepared<ChevronDown size={12}/></summary>{m.trace.map((t,j)=><div key={j}><b>{t.specialist.replace('_',' ')}</b><span>{t.tools.join(', ')}</span><Markdown>{t.result.summary}</Markdown></div>)}</details>:null}</div>)}{busy&&<GenerationLoader task="conversation"/>}{error&&<div className="error" role="alert">{error}{loading===false&&messages.length===0&&<button className="text-button" onClick={()=>void load()}>Reload history</button>}</div>}</div><form className="chat-input" onSubmit={e=>{e.preventDefault();void send(input)}}><input aria-label="Message CareerBuddy" value={input} onChange={e=>setInput(e.target.value)} placeholder="Message CareerBuddy…" maxLength={3000}/><button disabled={busy||loading||!input.trim()} aria-label="Send message"><ArrowUp size={19}/></button></form></section>
}
