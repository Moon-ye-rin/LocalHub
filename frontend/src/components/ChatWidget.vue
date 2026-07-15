<script setup lang="ts">
import { Bot, ExternalLink, MessageCircle, Send, X } from '@lucide/vue'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { sendChat } from '@/services/chat'
import { getApiErrorMessage } from '@/services/api'
import type { ChatMessage, ChatReference } from '@/types'

const { t, locale } = useI18n()
const router = useRouter()
const open = ref(false)
const input = ref('')
const loading = ref(false)
const error = ref('')
const scroller = ref<HTMLElement | null>(null)
const references = ref<ChatReference[]>([])
const sourceNotice = ref(t('chat.source'))
const initial = computed<ChatMessage>(() => ({ role: 'assistant', content: t('chat.greeting') }))
const messages = ref<ChatMessage[]>([initial.value])
const quickQuestions = computed(() => [t('chat.quick1'), t('chat.quick2'), t('chat.quick3'), t('chat.quick4')])

onMounted(() => {
  try {
    const key = `localhub-chat-${locale.value}`
    const stored = JSON.parse(localStorage.getItem(key) || '[]') as ChatMessage[]
    if (Array.isArray(stored) && stored.length) messages.value = stored
  } catch { localStorage.removeItem(`localhub-chat-${locale.value}`) }
})

watch(locale, () => {
  messages.value = [initial.value]
  references.value = []
  sourceNotice.value = t('chat.source')
  error.value = ''
})
watch(messages, (value) => localStorage.setItem(`localhub-chat-${locale.value}`, JSON.stringify(value.slice(-20))), { deep: true })
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
    const response = await sendChat(text, history, locale.value === 'en' ? 'en' : 'ko')
    messages.value.push({ role: 'assistant', content: response.reply })
    references.value = response.references
    sourceNotice.value = response.source_notice || t('chat.source')
  } catch (caught) { error.value = getApiErrorMessage(caught, t('errors.chat')) }
  finally { loading.value = false }
}

function openReference(reference: ChatReference): void {
  open.value = false
  if (reference.type === 'post') router.push(`/posts/${reference.id}`)
  else router.push(`/locations/${reference.id}`)
}

function clearChat(): void { messages.value = [initial.value]; references.value = []; error.value = '' }
</script>

<template>
  <button v-if="!open" class="chat-fab" type="button" :aria-label="$t('chat.open')" @click="open = true"><MessageCircle :size="25" /><span>{{ $t('chat.assistant') }}</span></button>
  <Teleport to="body">
    <section v-if="open" class="chat-panel" :aria-label="$t('chat.title')">
      <header class="chat-header">
        <span class="chat-avatar"><Bot :size="20" /></span>
        <div><strong>{{ $t('chat.title') }}</strong><small><i></i> {{ $t('chat.basedOnData') }}</small></div>
        <button class="chat-clear" type="button" @click="clearChat">{{ $t('chat.clear') }}</button>
        <button class="chat-close" type="button" :aria-label="$t('passwordModal.close')" @click="open = false"><X :size="20" /></button>
      </header>
      <div ref="scroller" class="chat-messages">
        <div v-for="(message, index) in messages" :key="index" :class="['chat-row', message.role]"><span v-if="message.role === 'assistant'" class="mini-avatar"><Bot :size="14" /></span><div class="chat-bubble">{{ message.content }}</div></div>
        <div v-if="loading" class="chat-row assistant"><span class="mini-avatar"><Bot :size="14" /></span><div class="chat-bubble typing"><i></i><i></i><i></i></div></div>
        <p v-if="error" class="chat-error">{{ error }}</p>
      </div>
      <div v-if="messages.length === 1" class="quick-questions"><button v-for="question in quickQuestions" :key="question" type="button" @click="submit(question)">{{ question }}</button></div>
      <div v-if="references.length" class="chat-sources"><small>{{ $t('chat.references') }}</small><button v-for="reference in references.slice(0, 5)" :key="`${reference.type}-${reference.id}`" type="button" @click="openReference(reference)">{{ reference.name }} <ExternalLink :size="12" /></button></div>
      <p class="chat-source-notice">{{ sourceNotice }}</p>
      <form class="chat-input-row" @submit.prevent="submit()"><input v-model="input" type="text" maxlength="1000" :placeholder="$t('chat.placeholder')" /><button type="submit" :disabled="!input.trim() || loading"><Send :size="18" /></button></form>
    </section>
  </Teleport>
</template>
