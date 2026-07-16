<script setup lang="ts">
import { Bot, ExternalLink, MessageCircle, Navigation, Send, X } from '@lucide/vue'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { sendChat } from '@/services/chat'
import { getApiErrorMessage } from '@/services/api'
import type { ChatMessage, ChatReference } from '@/types'

const router = useRouter()
const open = ref(false)
const input = ref('')
const loading = ref(false)
const error = ref('')
const scroller = ref<HTMLElement | null>(null)
const references = ref<ChatReference[]>([])
const sourceNotice = ref('출처: 한국관광공사 TourAPI 4.0 · 공공누리 제3유형')
// 경로 참조는 눈에 띄는 CTA 버튼으로, 나머지는 '참고한 정보' 목록으로 분리한다.
const routeReferences = computed(() => references.value.filter((item) => item.type === 'route'))
const infoReferences = computed(() => references.value.filter((item) => item.type !== 'route'))
const initial: ChatMessage = { role: 'assistant', content: '안녕하세요! LocalHub 챗봇이에요 😊\n서울·경기 공공데이터와 커뮤니티 글을 찾아드리고, "A에서 B 가는 길"처럼 물으면 지도 경로까지 안내해 드려요.\n자치구·시군 이름(예: 강남구, 수원시)과 유형(맛집·관광지·축제 등)을 함께 알려주시면 더 정확해요.' }
const messages = ref<ChatMessage[]>([initial])
const quickQuestions = ['강남구 맛집 추천', '종로구 문화시설', '경복궁에서 인사동 가는 길', '수원시 가볼만한 곳']

onMounted(() => {
  try {
    const stored = JSON.parse(localStorage.getItem('localhub-chat') || '[]') as ChatMessage[]
    if (Array.isArray(stored) && stored.length) messages.value = stored
  } catch { localStorage.removeItem('localhub-chat') }
})

watch(messages, (value) => localStorage.setItem('localhub-chat', JSON.stringify(value.slice(-20))), { deep: true })
watch([messages, loading], async () => { await nextTick(); if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight }, { deep: true })

async function submit(question?: string): Promise<void> {
  const text = (question ?? input.value).trim()
  if (!text || loading.value) return
  error.value = ''
  input.value = ''
  references.value = []
  const history = messages.value.slice(-12)
  messages.value.push({ role: 'user', content: text })
  loading.value = true
  try {
    const response = await sendChat(text, history)
    messages.value.push({ role: 'assistant', content: response.reply })
    references.value = response.references
    sourceNotice.value = response.source_notice
  } catch (caught) { error.value = getApiErrorMessage(caught, '챗봇 응답을 가져오지 못했습니다.') }
  finally { loading.value = false }
}

function openReference(reference: ChatReference): void {
  open.value = false
  if (reference.type === 'post') {
    router.push(`/posts/${reference.id}`)
  } else if (reference.type === 'route') {
    // id 형식: "출발contentid:도착contentid" → 상세 페이지에서 자동 경로 계산
    const [start, end] = reference.id.split(':')
    if (start && end) router.push(`/locations/${start}?to=${end}`)
  } else {
    router.push(`/locations/${reference.id}`)
  }
}

function clearChat(): void { messages.value = [initial]; references.value = []; error.value = '' }
</script>

<template>
  <button v-if="!open" class="chat-fab" type="button" aria-label="LocalHub 챗봇 열기" @click="open = true"><MessageCircle :size="25" /><span>AI 지역 도우미</span></button>
  <Teleport to="body">
    <section v-if="open" class="chat-panel" aria-label="LocalHub 챗봇">
      <header class="chat-header"><span class="chat-avatar"><Bot :size="20" /></span><div><strong>LocalHub 챗봇</strong><small><i></i> 실제 서울·경기 데이터 기반</small></div><button class="chat-clear" type="button" @click="clearChat">대화 초기화</button><button class="chat-close" type="button" @click="open = false"><X :size="20" /></button></header>
      <div ref="scroller" class="chat-messages">
        <div v-for="(message, index) in messages" :key="index" :class="['chat-row', message.role]"><span v-if="message.role === 'assistant'" class="mini-avatar"><Bot :size="14" /></span><div class="chat-bubble">{{ message.content }}</div></div>
        <div v-if="loading" class="chat-row assistant"><span class="mini-avatar"><Bot :size="14" /></span><div class="chat-bubble typing"><i></i><i></i><i></i></div></div>
        <p v-if="error" class="chat-error">{{ error }}</p>
      </div>
      <div v-if="messages.length === 1" class="quick-questions"><button v-for="question in quickQuestions" :key="question" type="button" @click="submit(question)">{{ question }}</button></div>
      <div v-if="routeReferences.length" class="chat-route-cta">
        <button v-for="reference in routeReferences" :key="`route-${reference.id}`" type="button" class="chat-route-btn" @click="openReference(reference)">
          <Navigation :size="16" /> <span>{{ reference.name.replace('🗺️ ', '') }}</span>
        </button>
      </div>
      <div v-if="infoReferences.length" class="chat-sources"><small>참고한 정보</small><button v-for="reference in infoReferences.slice(0, 5)" :key="`${reference.type}-${reference.id}`" type="button" @click="openReference(reference)">{{ reference.name }} <ExternalLink :size="12" /></button></div>
      <p class="chat-source-notice">{{ sourceNotice }}</p>
      <form class="chat-input-row" @submit.prevent="submit()"><input v-model="input" type="text" maxlength="1000" placeholder="서울·경기 지역정보를 물어보세요" /><button type="submit" :disabled="!input.trim() || loading"><Send :size="18" /></button></form>
    </section>
  </Teleport>
</template>
