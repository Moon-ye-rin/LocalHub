<script setup lang="ts">
import { X } from '@lucide/vue'
import { ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  title: string
  description: string
  confirmText?: string
  danger?: boolean
  loading?: boolean
  error?: string
}>()

const emit = defineEmits<{
  close: []
  confirm: [password: string]
}>()

const password = ref('')

watch(
  () => props.open,
  (value) => {
    if (value) password.value = ''
  },
)

function submit(): void {
  if (password.value.trim()) emit('confirm', password.value)
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="emit('close')">
      <section class="modal-card" role="dialog" aria-modal="true" :aria-label="title">
        <button class="modal-close" type="button" aria-label="닫기" @click="emit('close')"><X :size="20" /></button>
        <h2>{{ title }}</h2>
        <p>{{ description }}</p>
        <form @submit.prevent="submit">
          <label class="field-label" for="password-modal">수정용 비밀번호</label>
          <input id="password-modal" v-model="password" class="form-input" type="password" autocomplete="current-password" placeholder="비밀번호 입력" autofocus />
          <p v-if="error" class="form-error">{{ error }}</p>
          <div class="modal-actions">
            <button type="button" class="button button-ghost" @click="emit('close')">취소</button>
            <button type="submit" :class="['button', danger ? 'button-danger' : 'button-primary']" :disabled="!password.trim() || loading">
              {{ loading ? '처리 중...' : (confirmText || '확인') }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </Teleport>
</template>
