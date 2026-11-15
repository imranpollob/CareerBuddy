import { useEffect, useId, useRef } from 'react'
import { X } from 'lucide-react'

export function Modal({title, children, onClose}: {title: string; children: React.ReactNode; onClose: () => void}) {
  const ref = useRef<HTMLDialogElement>(null)
  const headingId = useId()
  useEffect(() => { ref.current?.showModal(); return () => ref.current?.close() }, [])
  return <dialog ref={ref} onCancel={onClose} className="modal" aria-labelledby={headingId}><div className="modal-head"><h2 id={headingId}>{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={onClose}><X size={20}/></button></div><div className="modal-body">{children}</div></dialog>
}
