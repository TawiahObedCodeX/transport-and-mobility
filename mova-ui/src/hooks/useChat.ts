import { useCallback, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { sendMessage } from '@/lib/api'
import { useChatStore } from '@/stores/chatStore'
import { generateId } from '@/lib/utils'

export function useChat() {
  const {
    activeSessionId,
    sessions,
    isLoading,
    error,
    createSession,
    addMessage,
    setLoading,
    setError,
    clearError,
    updateSessionTitle,
  } = useChatStore()

  // AbortController ref — cancels previous request when user sends a new one
  const abortRef = useRef<AbortController | null>(null)

  // StrictMode guard: useRef prevents the mutation from firing twice
  // in React 19 StrictMode development mode
  const pendingRef = useRef(false)

  const mutation = useMutation({
    mutationFn: async ({
      message,
      sessionId,
    }: {
      message: string
      sessionId: string
    }) => {
      return sendMessage(message, sessionId, abortRef.current?.signal)
    },
    onMutate: () => {
      pendingRef.current = true
    },
    onSuccess: (data) => {
      pendingRef.current = false
      addMessage({
        id: generateId(),
        role: 'assistant',
        content: data.response,
        timestamp: Date.now(),
      })
      if (activeSessionId) {
        updateSessionTitle(activeSessionId)
      }
      setLoading(false)
    },
    onError: (err: Error) => {
      pendingRef.current = false
      if (err.name === 'AbortError') return // cancelled, do nothing
      setError(err.message)
      setLoading(false)
      addMessage({
        id: generateId(),
        role: 'assistant',
        content: `I encountered an issue: ${err.message}\n\nPlease try again in a moment.`,
        timestamp: Date.now(),
      })
    },
  })

  const send = useCallback(
    async (content: string) => {
      // StrictMode guard: if a mutation is already pending, ignore
      if (pendingRef.current) return

      const trimmed = content.trim()
      if (!trimmed || isLoading) return

      clearError()

      // Cancel any in-flight request
      if (abortRef.current) {
        abortRef.current.abort()
      }
      abortRef.current = new AbortController()

      let sessionId = activeSessionId
      if (!sessionId) {
        sessionId = createSession()
      }

      addMessage({
        id: generateId(),
        role: 'user',
        content: trimmed,
        timestamp: Date.now(),
      })

      setLoading(true)
      mutation.mutate({ message: trimmed, sessionId })
    },
    [
      activeSessionId,
      isLoading,
      clearError,
      createSession,
      addMessage,
      setLoading,
      mutation,
    ],
  )

  return {
    send,
    isLoading,
    error,
    clearError,
    sessions,
    activeSessionId,
  }
}
