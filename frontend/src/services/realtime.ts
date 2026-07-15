import { getClientKey, getWebSocketUrl } from './api'

export interface RealtimePostNotification {
  id: number
  title: string
  category: string
  region: string
  district: string
}

export type RealtimeEvent =
  | { type: 'connected' | 'presence'; online_count: number; server_time?: string }
  | { type: 'post_created'; post: RealtimePostNotification; created_at: string }
  | { type: 'pong' }

export function createRealtimeSocket(): WebSocket {
  const url = new URL(getWebSocketUrl())
  url.searchParams.set('client_key', getClientKey())
  return new WebSocket(url)
}
