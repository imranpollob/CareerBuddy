import {useEffect,useRef,useState} from 'react'
import {ArrowUp,Bot,Sparkles,ChevronDown} from 'lucide-react'
import {api,type ChatResponse,type Role,type Conversation} from '../api'
interface Message {text:string;user?:boolean;trace?:ChatResponse['delegations'];specialists?:string[]}
export function Chat({mode,role,onResult}:{mode:string;role:Role;onResult:(result:ChatResponse)=>Promise<void>}){
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
  const suggestions=role==='candidate'?['Evaluate my profile','Show my next learning topic','Take my next assessment','Find matching jobs']:['Find candidates for my jobs','Analyze market requirements']
  return <section className="chat-panel card main-chat"><div className="chat-heading"><div className="bot-icon"><Bot size={21}/></div><div><h2>Career assistant</h2><span><i className="status-dot"/>{mode==='bedrock'?'CareerBuddy · powered by Amazon Bedrock':'Offline preview · simulated AI'}</span></div></div><div ref={scroll} className="chat-content" aria-live="polite">{loading?<p className="muted">Loading your conversation…</p>:messages.length===0&&<div className="chat-welcome"><Sparkles size={30}/><h2>Your next step starts here.</h2><p>Let’s connect your experience, learning, and opportunities to a clear career plan.</p><div className="suggestions">{suggestions.map(s=><button key={s} onClick={()=>void send(s)}>{s}<span aria-hidden="true">↗</span></button>)}</div></div>}{messages.map((m,i)=><div key={i} className={`chat-message ${m.user?'user':''}`}><small>{m.user?'YOU':'CAREERBUDDY'}</small><p>{m.text}</p>{m.trace&&m.trace.length>0?<details className="trace"><summary>How this answer was prepared<ChevronDown size={12}/></summary>{m.trace.map((t,j)=><div key={j}><b>{t.specialist.replace('_',' ')}</b><span>{t.tools.join(', ')}</span><p>{t.result.summary}</p></div>)}</details>:!!m.specialists?.length&&<small className="saved-specialists">With {m.specialists.join(', ').replaceAll('_',' ')} · saved conversation</small>}</div>)}{busy&&<p className="muted" role="status">CareerBuddy is working with its specialists…</p>}{error&&<div className="error" role="alert">{error}{loading===false&&messages.length===0&&<button className="text-button" onClick={()=>void load()}>Reload history</button>}</div>}</div><form className="chat-input" onSubmit={e=>{e.preventDefault();void send(input)}}><input aria-label="Message CareerBuddy" value={input} onChange={e=>setInput(e.target.value)} placeholder="What would you like to work on?" maxLength={3000}/><button disabled={busy||loading||!input.trim()} aria-label="Send message"><ArrowUp size={19}/></button></form><p className="chat-footnote">Your conversation is saved privately. AI guidance complements your judgment.</p></section>
}
