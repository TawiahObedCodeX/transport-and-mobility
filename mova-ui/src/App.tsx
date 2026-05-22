import { useEffect, useRef } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppLayout } from '@/components/layout/AppLayout'
import { ChatContainer } from '@/components/chat/ChatContainer'
import { useChatStore } from '@/stores/chatStore'
import { useUiStore } from '@/stores/uiStore'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 2,
    },
  },
})

function AppContent() {
  const { sessions, createSession } = useChatStore()
  const { setMounted } = useUiStore()

  // StrictMode guard: useRef ensures effects only fire once
  const mountedRef = useRef(false)

  useEffect(() => {
    if (mountedRef.current) return
    mountedRef.current = true
    setMounted(true)
  }, [setMounted])

  useEffect(() => {
    if (sessions.length === 0) {
      createSession()
    }
    // Intentionally run only once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <AppLayout>
      <ChatContainer />
    </AppLayout>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}
