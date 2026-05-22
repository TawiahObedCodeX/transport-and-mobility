import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage as ChatMessageType } from '@/types/chat'
import { cn, formatTime } from '@/lib/utils'
import { User, Bot } from 'lucide-react'

interface ChatMessageProps {
  message: ChatMessageType
  isLatest?: boolean
}

export function ChatMessage({ message, isLatest }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
      className={cn(
        'flex items-start gap-3 px-4 py-2',
        isUser ? 'justify-end' : 'justify-start',
      )}
    >
      {/* Assistant avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 ring-1 ring-primary/20">
          <Bot className="w-4 h-4 text-primary" />
        </div>
      )}

      {/* Bubble */}
      <div
        className={cn(
          'max-w-[75%] md:max-w-[65%]',
          isUser ? 'order-1' : 'order-1',
        )}
      >
        <div
          className={cn(
            'px-4 py-3 text-sm leading-relaxed',
            isUser
              ? 'bg-primary text-primary-foreground rounded-2xl rounded-tr-sm shadow-sm'
              : 'bg-muted/40 border rounded-2xl rounded-tl-sm',
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-slate prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children, ...props }) {
                    const isInline = !className
                    if (isInline) {
                      return (
                        <code
                          className="bg-muted/80 px-1.5 py-0.5 rounded text-sm font-mono"
                          {...props}
                        >
                          {children}
                        </code>
                      )
                    }
                    return (
                      <div className="relative group my-2">
                        <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(
                                String(children).replace(/\n$/, ''),
                              )
                            }}
                            className="text-[11px] text-muted-foreground/50 hover:text-muted-foreground bg-background/80 px-2 py-1 rounded-md border"
                          >
                            Copy
                          </button>
                        </div>
                        <pre className="bg-slate-50 border rounded-xl p-4 overflow-x-auto">
                          <code className={className} {...props}>
                            {children}
                          </code>
                        </pre>
                      </div>
                    )
                  },
                  pre({ children }) {
                    return <>{children}</>
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <p
          className={cn(
            'text-[11px] text-muted-foreground/40 mt-1 px-1',
            isUser ? 'text-right' : 'text-left',
          )}
        >
          {formatTime(message.timestamp)}
          {isLatest && !isUser && (
            <span className="ml-2 text-primary/40">●</span>
          )}
        </p>
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0 shadow-sm">
          <User className="w-4 h-4 text-primary-foreground" />
        </div>
      )}
    </motion.div>
  )
}
