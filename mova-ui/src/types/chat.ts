export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: number
  updatedAt: number
}

export interface ChatRequest {
  message: string
  session_id: string
}

export interface ChatResponse {
  response: string
  session_id: string
}

export interface StreamChunk {
  content: string
  done: boolean
}

export type MessageStatus = 'sending' | 'sent' | 'error'
