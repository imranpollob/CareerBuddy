import {useEffect,useRef,useState,type ReactNode} from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {Check,Copy} from 'lucide-react'
function CodeBlock({children}:{children?:ReactNode}){
 const ref=useRef<HTMLPreElement>(null)
 const timer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined)
 const [state,setState]=useState<'ready'|'copied'|'error'>('ready')
 useEffect(()=>()=>{if(timer.current)clearTimeout(timer.current)},[])
 async function copy(){try{await navigator.clipboard.writeText(ref.current?.textContent||'');setState('copied')}catch{setState('error')}if(timer.current)clearTimeout(timer.current);timer.current=setTimeout(()=>setState('ready'),2200)}
 return <div className="markdown-code"><div className="code-toolbar"><span>Code</span><button type="button" onClick={()=>void copy()} aria-label={state==='copied'?'Code copied':'Copy code'}>{state==='copied'?<Check size={14}/>:<Copy size={14}/>}<span role="status">{state==='copied'?'Copied':state==='error'?'Copy unavailable':'Copy'}</span></button></div><pre ref={ref}>{children}</pre></div>
}
export function Markdown({children}:{children:string}){
 // Some model responses wrap an entire answer in a Markdown code fence.
 const text=children.trim().replace(/^```(?:markdown|md)\s*\n([\s\S]*?)\n```$/i,'$1')
 return <div className="markdown-content"><ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{
  pre:({children})=><CodeBlock>{children}</CodeBlock>,
  table:({children})=><div className="markdown-table"><table>{children}</table></div>,
  a:({href,children})=>href&&/^https?:\/\//i.test(href)?<a href={href} target="_blank" rel="noopener noreferrer">{children}</a>:<span>{children}</span>,
  img:()=>null,
 }}>{text}</ReactMarkdown></div>
}
