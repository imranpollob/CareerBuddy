import { useState } from 'react'
import { ArrowUp, Bot, Sparkles, ChevronDown } from 'lucide-react'
import { api, type ChatResponse, type Role } from '../api'

interface Message { text: string; user?: boolean; trace?: ChatResponse['delegations'] }
export function Chat({mode, role, onResult}: {mode: string; role: Role; onResult: (result: ChatResponse) => Promise<void>}) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function send(text: string) {
    if (!text.trim() || busy) return
    setInput(''); setError(''); setMessages(m => [...m,{text,user:true}]); setBusy(true)
    try {
      const response = await api<ChatResponse>('/chat','POST',{message:text})
      setMessages(m => [...m,{text:response.message, trace:response.delegations}]); await onResult(response)
    } catch(e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  const suggestions = role === 'candidate' ? ['What skills are in demand?', 'Prepare a Python assessment', 'Build my learning roadmap', 'Find jobs that match my skills'] : ['Find candidates for my jobs', 'Analyze market requirements']
  return <aside className="chat-panel card"><div className="chat-heading"><div className="bot-icon"><Bot size={21}/></div><div><h3>SkillPilot assistant</h3><span><i className="status-dot"/>{mode === 'bedrock' ? 'Your AI career assistant' : 'Offline preview'}</span></div></div>
    <div className="chat-content" aria-live="polite"><div className="assistant-intro"><Sparkles size={24}/><h3>How can I help?</h3><p>{role === 'candidate' ? 'Explore what employers need, demonstrate your skills, and turn the gaps into a plan.' : 'Explore job requirements and discover candidates with assessment evidence.'}</p></div>
      {messages.length === 0 && <div className="suggestions">{suggestions.map(s => <button key={s} disabled={busy} onClick={() => void send(s)}>{s}<span aria-hidden="true">↗</span></button>)}</div>}
      {messages.map((m,i) => <div key={i} className={`chat-message ${m.user ? 'user' : ''}`}><small>{m.user ? 'YOU' : 'SKILLPILOT'}</small><p>{m.text}</p>{m.trace && m.trace.length > 0 && <details className="trace"><summary>How this answer was prepared <ChevronDown size={12}/></summary>{m.trace.map((t,j) => <div key={j}><b>{t.specialist.replace('_',' ')}</b><span>{t.tools.join(', ')}</span><p>{t.result.summary}</p></div>)}</details>}</div>)}
      {busy && <p className="muted text-sm">SkillPilot is working with its tools…</p>}
      {error && <div className="error" role="alert">{error}<button className="text-button" onClick={() => void send(messages.filter(m=>m.user).at(-1)?.text || 'Hello')}>Retry</button></div>}
    </div><form className="chat-input" onSubmit={e => {e.preventDefault(); void send(input)}}><input aria-label="Message SkillPilot" value={input} onChange={e=>setInput(e.target.value)} placeholder="Ask SkillPilot…" maxLength={3000}/><button disabled={busy || !input.trim()} aria-label="Send message"><ArrowUp size={19}/></button></form><p className="chat-footnote">AI guidance complements your own judgment.</p>
  </aside>
}
