import { useChatStore } from '@/stores/chatStore'
import { useChat } from '@/hooks/useChat'
import { useAutoScroll } from '@/hooks/useAutoScroll'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { TypingIndicator } from './TypingIndicator'
import { WelcomeScreen } from './WelcomeScreen'
import { MessageSquare } from 'lucide-react'
import { useUiStore } from '@/stores/uiStore'

export function ChatContainer() {
  const { getActiveMessages, isLoading } = useChatStore()
  const messages = getActiveMessages()
  const { send } = useChat()
  const { containerRef, handleScroll } = useAutoScroll([messages, isLoading])
  const { setMobileNavOpen } = useUiStore()

  const hasMessages = messages.length > 0

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Floating header for mobile */}
      <div className="lg:hidden flex items-center justify-between px-4 py-3 border-b bg-background/80 backdrop-blur-xl shrink-0">
        <button
          onClick={() => setMobileNavOpen(true)}
          className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center -ml-1"
        >
          <MessageSquare className="w-4 h-4 text-muted-foreground" />
        </button>
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold">MOVA</span>
        </div>
        <div className="w-8" />
      </div>

      {/* Messages area */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto scrollbar-thin"
      >
        {hasMessages ? (
          <div className="max-w-3xl mx-auto py-4 space-y-1">
            {messages.map((msg, i) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                isLatest={i === messages.length - 1}
              />
            ))}
            {isLoading && <TypingIndicator />}
          </div>
        ) : (
          <WelcomeScreen />
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={send} isLoading={isLoading} />
    </div>
  )
}
