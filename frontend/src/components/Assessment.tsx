import { useState } from 'react'
import { CheckCircle2, ShieldCheck } from 'lucide-react'
import { api, type Assessment as Attempt, skillLabel } from '../api'
import { Modal } from './Modal'

export function Assessment({attempt, onClose, onSaved}: {attempt: Attempt; onClose: () => void; onSaved: () => Promise<void>}) {
  const [data, setData] = useState(attempt)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try { setData(await api<Attempt>(`/assessments/${data.id}/submit`, 'POST', {answers})); await onSaved() }
    catch(e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  return <Modal title={`${skillLabel(data.skill)} · ${data.competency_id?"Competency check":"Fundamentals check"}`} onClose={onClose}>
    <div className="notice"><ShieldCheck size={18}/><span>4 objective questions · 75% to pass. Graded on the server. This is a fundamentals check, not a certification.</span></div>
    {data.competency_title&&<h3 className="lesson-section-title">{data.competency_title}</h3>}{data.personalized_context&&<p className="assessment-context">{data.personalized_context}</p>}
    <p className="muted text-sm assessment-provenance">{data.kind==='llm_generated_v1'?'AI-generated for your skill profile':data.kind==='mock_generated_v1'?'Offline assessment fixture':'Fixed fundamentals assessment'}</p>
    {data.result ? <><div className={`result ${data.result.passed ? 'passed' : 'needs-practice'}`}><CheckCircle2 size={32}/><strong>{data.result.score}%</strong><h3>{data.result.passed ? 'Evidence recorded' : 'A starting point to build on'}</h3><p>{data.result.passed ? data.competency_id?'This competency is recorded. Complete the full pathway to support the broader skill.':'Your foundational evidence and job matches are updated.' : 'Open the lesson for this skill, then take a fresh assessment.'}</p></div>
      {data.result.feedback.map((f,i) => <div className="feedback" key={f.question_id}><b>{i+1}. {f.correct ? 'Correct' : 'Keep practicing'}</b><p>{f.explanation}</p></div>)}<button className="button primary wide" onClick={onClose}>Back to my workspace</button></>
    : <form onSubmit={submit}>{data.questions.map((q,i) => <fieldset key={q.id} className="question"><legend><span>{i+1}</span>{q.prompt}</legend>{q.choices.map((c,index) => <label className={`choice ${answers[q.id] === index ? 'selected' : ''}`} key={c}><input required type="radio" name={q.id} value={index} checked={answers[q.id]===index} onChange={() => setAnswers({...answers,[q.id]:index})}/>{c}</label>)}</fieldset>)}
      {error && <p role="alert" className="error">{error}</p>}<button className="button primary wide" disabled={busy || Object.keys(answers).length !== data.questions.length}>{busy ? 'Recording evidence…' : 'Submit assessment'}</button></form>}
  </Modal>
}
