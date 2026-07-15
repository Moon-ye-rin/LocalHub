<script setup lang="ts">
import { Bell, MapPin, Menu, Trash2, Users, X } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { createRealtimeSocket, type RealtimeEvent, type RealtimePostNotification } from '@/services/realtime'

interface NotificationItem extends RealtimePostNotification {
  createdAt: string
}

const route = useRoute()
const mobileOpen = ref(false)
const notificationOpen = ref(false)
const notificationListRef = ref<HTMLElement | null>(null)
const onlineCount = ref(0)
const unreadCount = ref(0)
const notifications = ref<NotificationItem[]>([])
const realtimeConnected = ref(false)
let socket: WebSocket | null = null
let reconnectTimer: number | undefined
let pingTimer: number | undefined
let intentionallyClosed = false
let dragActive = false
let dragStartY = 0
let dragStartScrollTop = 0
let draggedSincePointerDown = false

const navItems = [
  { label: '홈', to: '/' },
  { label: '게시판', to: '/board' },
  { label: '지역정보', to: '/locations' },
  { label: '대시보드', to: '/dashboard' },
]

function isActive(to: string): boolean {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to) || (to === '/board' && route.path.startsWith('/posts'))
}

function notificationKey(item: NotificationItem): string {
  return `${item.id}-${item.createdAt}`
}

function connectRealtime(): void {
  window.clearTimeout(reconnectTimer)
  try {
    socket = createRealtimeSocket()
  } catch {
    scheduleReconnect()
    return
  }

  socket.addEventListener('open', () => {
    realtimeConnected.value = true
    window.clearInterval(pingTimer)
    pingTimer = window.setInterval(() => {
      if (socket?.readyState === WebSocket.OPEN) socket.send('ping')
    }, 20000)
  })

  socket.addEventListener('message', (event) => {
    try {
      const payload = JSON.parse(event.data) as RealtimeEvent
      if (payload.type === 'connected' || payload.type === 'presence') {
        onlineCount.value = payload.online_count
      } else if (payload.type === 'post_created') {
        notifications.value.unshift({ ...payload.post, createdAt: payload.created_at })
        notifications.value = notifications.value.slice(0, 50)
        unreadCount.value += 1
      }
    } catch {
      // Ignore malformed messages and keep the connection alive.
    }
  })

  socket.addEventListener('close', () => {
    realtimeConnected.value = false
    window.clearInterval(pingTimer)
    if (!intentionallyClosed) scheduleReconnect()
  })

  socket.addEventListener('error', () => socket?.close())
}

function scheduleReconnect(): void {
  window.clearTimeout(reconnectTimer)
  reconnectTimer = window.setTimeout(connectRealtime, 3000)
}

function toggleNotifications(): void {
  notificationOpen.value = !notificationOpen.value
  if (notificationOpen.value) unreadCount.value = 0
}

function closeNotifications(): void {
  notificationOpen.value = false
  unreadCount.value = 0
}

function deleteNotification(item: NotificationItem): void {
  const key = notificationKey(item)
  notifications.value = notifications.value.filter((notification) => notificationKey(notification) !== key)
}

function startNotificationDrag(event: PointerEvent): void {
  const target = event.target as HTMLElement
  if (target.closest('button')) return
  const element = notificationListRef.value
  if (!element || element.scrollHeight <= element.clientHeight) return
  dragActive = true
  draggedSincePointerDown = false
  dragStartY = event.clientY
  dragStartScrollTop = element.scrollTop
  element.setPointerCapture(event.pointerId)
  element.classList.add('dragging')
}

function moveNotificationDrag(event: PointerEvent): void {
  if (!dragActive || !notificationListRef.value) return
  const delta = event.clientY - dragStartY
  if (Math.abs(delta) > 4) draggedSincePointerDown = true
  notificationListRef.value.scrollTop = dragStartScrollTop - delta
  if (draggedSincePointerDown) event.preventDefault()
}

function endNotificationDrag(event: PointerEvent): void {
  if (!dragActive) return
  const element = notificationListRef.value
  dragActive = false
  element?.classList.remove('dragging')
  if (element?.hasPointerCapture(event.pointerId)) element.releasePointerCapture(event.pointerId)
  window.setTimeout(() => { draggedSincePointerDown = false }, 0)
}

function suppressDraggedClick(event: MouseEvent): void {
  if (!draggedSincePointerDown) return
  event.preventDefault()
  event.stopPropagation()
  draggedSincePointerDown = false
}

function formatNotificationTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '방금 전'
  return new Intl.DateTimeFormat('ko-KR', { hour: '2-digit', minute: '2-digit' }).format(date)
}

onMounted(connectRealtime)
onBeforeUnmount(() => {
  intentionallyClosed = true
  window.clearTimeout(reconnectTimer)
  window.clearInterval(pingTimer)
  socket?.close()
})
</script>

<template>
  <header class="site-header">
    <div class="page-container header-inner">
      <RouterLink to="/" class="brand" @click="mobileOpen = false">
        <span class="brand-icon"><MapPin :size="19" /></span>
        <span class="brand-copy">
          <strong>LocalHub</strong>
          <small>서울·경기</small>
        </span>
      </RouterLink>

      <div class="realtime-tools">
        <div class="notification-center">
          <button
            type="button"
            class="notification-button"
            :class="{ active: notificationOpen }"
            aria-label="새 게시글 알림"
            @click="toggleNotifications"
          >
            <Bell :size="19" />
            <span v-if="unreadCount" class="notification-badge">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
          </button>
          <div v-if="notificationOpen" class="notification-popover">
            <header>
              <strong>새 게시글 알림</strong>
              <small>{{ realtimeConnected ? '실시간 연결됨' : '재연결 중' }}</small>
            </header>
            <div v-if="notifications.length === 0" class="notification-empty">새로 등록된 게시글이 없습니다.</div>
            <div
              v-else
              ref="notificationListRef"
              class="notification-list"
              @pointerdown="startNotificationDrag"
              @pointermove="moveNotificationDrag"
              @pointerup="endNotificationDrag"
              @pointercancel="endNotificationDrag"
              @click.capture="suppressDraggedClick"
            >
              <div
                v-for="item in notifications"
                :key="notificationKey(item)"
                class="notification-item-row"
              >
                <RouterLink
                  :to="`/posts/${item.id}`"
                  class="notification-item"
                  @click="closeNotifications"
                >
                  <span>{{ item.region }} {{ item.district }} · {{ item.category }}</span>
                  <strong>{{ item.title }}</strong>
                  <time>{{ formatNotificationTime(item.createdAt) }}</time>
                </RouterLink>
                <button
                  type="button"
                  class="notification-delete"
                  aria-label="알림 삭제"
                  title="알림 삭제"
                  @click.stop="deleteNotification(item)"
                >
                  <Trash2 :size="15" />
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="online-status" :class="{ connected: realtimeConnected }" title="현재 접속자 현황">
          <Users :size="16" />
          <span>{{ onlineCount }}명 접속</span>
        </div>
      </div>

      <nav class="desktop-nav" aria-label="주요 메뉴">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="['nav-link', { active: isActive(item.to) }]"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <RouterLink to="/posts/new" class="button button-primary desktop-write">글쓰기</RouterLink>

      <button class="mobile-menu-button" type="button" aria-label="메뉴 열기" @click="mobileOpen = !mobileOpen">
        <X v-if="mobileOpen" :size="22" />
        <Menu v-else :size="22" />
      </button>
    </div>

    <div v-if="mobileOpen" class="mobile-nav">
      <div class="page-container mobile-nav-inner">
        <div class="mobile-presence"><Users :size="15" /> 현재 {{ onlineCount }}명 접속</div>
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="['mobile-nav-link', { active: isActive(item.to) }]"
          @click="mobileOpen = false"
        >
          {{ item.label }}
        </RouterLink>
        <RouterLink to="/posts/new" class="button button-primary" @click="mobileOpen = false">새 글 작성</RouterLink>
      </div>
    </div>
  </header>
</template>
