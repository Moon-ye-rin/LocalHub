import axios from 'axios'

const CLIENT_KEY_NAME = 'localhub-client-key'
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function getWebSocketUrl(path = '/ws/notifications'): string {
  const url = new URL(API_BASE_URL)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = path
  url.search = ''
  url.hash = ''
  return url.toString()
}

export function getClientKey(): string {
  let key = localStorage.getItem(CLIENT_KEY_NAME)
  if (!key) {
    key = crypto.randomUUID()
    localStorage.setItem(CLIENT_KEY_NAME, key)
  }
  return key
}

export function resolveApiAsset(path: string): string {
  if (!path) return ''
  if (/^https?:\/\//i.test(path) || path.startsWith('data:') || path.startsWith('blob:')) return path
  return `${API_BASE_URL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  config.headers['X-Client-Key'] = getClientKey()
  return config
})

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const message = error.response?.data?.message
    if (typeof message === 'string' && message) return message
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail) return detail
    if (!error.response) return '서버에 연결할 수 없습니다. 백엔드 실행 상태를 확인해 주세요.'
  }
  return fallback
}

export default api
