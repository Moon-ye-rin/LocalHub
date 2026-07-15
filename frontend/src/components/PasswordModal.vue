<script setup lang="ts">
import { X } from '@lucide/vue'
import { ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  title: string
  description?: string
  confirmText?: string
  loading?: boolean
  error?: string
  danger?: boolean
}>()
const emit = defineEmits<{ close: []; confirm: [password: string] }>()
const password = ref('')

watch(() => props.open, (value) => { if (value) password.value = '' })
</script>

<template>
  <div v-if="open" class="modal-backdrop" @click.self="emit('close')">
    <section class="password-modal" role="dialog" aria-modal="true" :aria-label="title">
      <header>
        <div><h2>{{ title }}</h2><p v-if="description">{{ description }}</p></div>
        <button class="modal-close" type="button" :aria-label="$t('passwordModal.close')" @click="emit('close')"><X :size="20" /></button>
      </header>
      <form @submit.prevent="emit('confirm', password)">
        <label class="field-label" for="password-modal">{{ $t('passwordModal.label') }}</label>
        <input id="password-modal" v-model="password" class="form-input" type="password" autocomplete="current-password" :placeholder="$t('passwordModal.placeholder')" autofocus />
        <p v-if="error" class="form-error">{{ error }}</p>
        <div class="modal-actions">
          <button type="button" class="button button-ghost" @click="emit('close')">{{ $t('common.cancel') }}</button>
          <button type="submit" :class="['button', danger ? 'button-danger' : 'button-primary']" :disabled="loading || !password">
            {{ loading ? $t('common.processing') : (confirmText || $t('common.confirm')) }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>
