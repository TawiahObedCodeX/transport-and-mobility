import type { ChatRequest, ChatResponse } from '@/types/chat'

const API_URL = 'http://localhost:5000'

// Tracks in-flight requests for dedup at the API layer
let lastRequestKey = ''
let lastRequestTime = 0
const DEDUP_MS = 2000

export async function sendMessage(
  message: string,
  sessionId: string,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  // Client-side dedup: skip if same message+session was sent within 2s
  const key = `${sessionId}:${message.trim().toLowerCase()}`
  const now = Date.now()
  if (key === lastRequestKey && now - lastRequestTime < DEDUP_MS) {
    throw new Error('Duplicate request ignored')
  }
  lastRequestKey = key
  lastRequestTime = now

  const payload: ChatRequest = { message, session_id: sessionId }

  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail =
      (body as { detail?: string }).detail ??
      `Request failed with status ${response.status}`
    throw new Error(detail)
  }

  return response.json() as Promise<ChatResponse>
}

export async function healthCheck(signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`, { signal })
    return response.ok
  } catch {
    return false
  }
}
