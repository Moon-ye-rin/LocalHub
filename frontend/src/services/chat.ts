import api from './api'
import type { ApiResponse, ChatData, ChatMessage } from '@/types'

export async function sendChat(message: string, history: ChatMessage[]): Promise<ChatData> {
  const { data } = await api.post<ApiResponse<ChatData>>('/api/chat', {
    message,
    history: history.slice(-12),
  })
  return data.data
}
