import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'

export function AssistantDrawer({open,onClose,children}:{open:boolean;onClose:()=>void;children:React.ReactNode}){
  const ref=useRef<HTMLDialogElement>(null)
  useEffect(()=>{if(open&&!ref.current?.open)ref.current?.showModal();else if(!open&&ref.current?.open)ref.current.close()},[open])
  return <dialog ref={ref} className="assistant-drawer" aria-label="SkillPilot career assistant" onCancel={onClose}><button className="icon-button assistant-close" aria-label="Close assistant" onClick={onClose}><X size={20}/></button>{children}</dialog>
}
