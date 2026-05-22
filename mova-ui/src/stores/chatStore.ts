import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ChatMessage, ChatSession } from '@/types/chat'
import { generateId, getSessionTitle } from '@/lib/utils'

interface ChatState {
  sessions: ChatSession[]
  activeSessionId: string | null
  isLoading: boolean
  error: string | null

  getActiveSession: () => ChatSession | undefined
  getActiveMessages: () => ChatMessage[]
  createSession: () => string
  deleteSession: (id: string) => void
  setActiveSession: (id: string) => void
  addMessage: (message: ChatMessage) => void
  appendToLastAssistantMessage: (chunk: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  updateSessionTitle: (id: string) => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      sessions: [],
      activeSessionId: null,
      isLoading: false,
      error: null,

      getActiveSession: () => {
        const { sessions, activeSessionId } = get()
        return sessions.find((s) => s.id === activeSessionId)
      },

      getActiveMessages: () => {
        const session = get().getActiveSession()
        return session?.messages ?? []
      },

      createSession: () => {
        const id = generateId()
        const now = Date.now()
        const session: ChatSession = {
          id,
          title: 'New conversation',
          messages: [],
          createdAt: now,
          updatedAt: now,
        }
        set((state) => ({
          sessions: [session, ...state.sessions],
          activeSessionId: id,
        }))
        return id
      },

      deleteSession: (id: string) => {
        set((state) => {
          const filtered = state.sessions.filter((s) => s.id !== id)
          const wasActive = state.activeSessionId === id
          return {
            sessions: filtered,
            activeSessionId:
              wasActive ? (filtered[0]?.id ?? null) : state.activeSessionId,
          }
        })
      },

      setActiveSession: (id: string) => {
        set({ activeSessionId: id, error: null })
      },

      addMessage: (message: ChatMessage) => {
        set((state) => {
          const session = state.sessions.find(
            (s) => s.id === state.activeSessionId,
          )
          if (!session) return state

          const updated: ChatSession = {
            ...session,
            messages: [...session.messages, message],
            updatedAt: Date.now(),
          }

          return {
            sessions: state.sessions.map((s) =>
              s.id === updated.id ? updated : s,
            ),
          }
        })
      },

      appendToLastAssistantMessage: (chunk: string) => {
        set((state) => {
          const session = state.sessions.find(
            (s) => s.id === state.activeSessionId,
          )
          if (!session) return state

          const messages = [...session.messages]
          const lastMsg = messages[messages.length - 1]

          if (lastMsg && lastMsg.role === 'assistant') {
            messages[messages.length - 1] = {
              ...lastMsg,
              content: lastMsg.content + chunk,
            }
          }

          return {
            sessions: state.sessions.map((s) =>
              s.id === session.id
                ? { ...session, messages, updatedAt: Date.now() }
                : s,
            ),
          }
        })
      },

      setLoading: (loading: boolean) => set({ isLoading: loading }),

      setError: (error: string | null) => set({ error }),

      clearError: () => set({ error: null }),

      updateSessionTitle: (id: string) => {
        set((state) => {
          const session = state.sessions.find((s) => s.id === id)
          if (!session) return state
          return {
            sessions: state.sessions.map((s) =>
              s.id === id
                ? { ...s, title: getSessionTitle(s.messages) }
                : s,
            ),
          }
        })
      },
    }),
    {
      name: 'mova-chat-store',
      partialize: (state) => ({
        sessions: state.sessions,
        activeSessionId: state.activeSessionId,
      }),
    },
  ),
)
