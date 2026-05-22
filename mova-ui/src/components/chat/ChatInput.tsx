import { useState, useRef, useEffect } from 'react'
import { ArrowUp, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading: boolean
}

const SUGGESTIONS = [
  'Plan a journey from London to Paris by train',
  'Compare electric vs hydrogen buses',
  'What is Vision Zero in road safety?',
  'Explain MaaS (Mobility as a Service)',
]

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [input, setInput] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(true)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  // Double-send lock: prevents React 19 StrictMode from calling onSend twice
  const sendingRef = useRef(false)

  useEffect(() => {
    if (!isLoading && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [isLoading])

  const adjustHeight = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }

  const handleSubmit = () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading || sendingRef.current) return
    sendingRef.current = true
    onSend(trimmed)
    // Reset lock after a tick so React StrictMode's double-invoke
    // sees the same ref value and skips the second call
    setTimeout(() => { sendingRef.current = false }, 0)
    setInput('')
    setShowSuggestions(false)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="border-t bg-gradient-to-t from-background via-background to-transparent pt-4 pb-2 px-4">
      {showSuggestions && !isLoading && (
        <div className="max-w-3xl mx-auto mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-3.5 h-3.5 text-primary/60" />
            <span className="text-xs text-muted-foreground/60 font-medium">
              Suggested questions
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => {
                  setInput(s)
                  setShowSuggestions(false)
                  setTimeout(() => textareaRef.current?.focus(), 0)
                }}
                className="text-xs text-muted-foreground/70 bg-muted/40 hover:bg-muted/80 border px-3 py-1.5 rounded-xl transition-all duration-200 hover:border-primary/30 active:scale-[0.97]"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="max-w-3xl mx-auto">
        <div
          className={cn(
            'flex items-end gap-2 bg-background border rounded-2xl px-4 py-3 transition-all duration-200 shadow-sm',
            'focus-within:border-primary/40 focus-within:shadow-md',
            'hover:border-muted-foreground/20',
          )}
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              adjustHeight()
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask MOVA about transport, routes, schedules..."
            rows={1}
            disabled={isLoading}
            className="flex-1 bg-transparent resize-none outline-none text-sm leading-relaxed placeholder:text-muted-foreground/40 disabled:opacity-50 min-h-[24px] max-h-[160px]"
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading || !input.trim()}
            className={cn(
              'w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-all duration-200',
              input.trim() && !isLoading
                ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm active:scale-[0.92]'
                : 'bg-muted text-muted-foreground/40 cursor-not-allowed',
            )}
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </div>
        <p className="text-center text-[11px] text-muted-foreground/25 mt-2">
          MOVA may produce inaccurate information. Verify important details.
        </p>
      </div>
    </div>
  )
}
