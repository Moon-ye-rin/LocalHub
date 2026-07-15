<script setup lang="ts">
import { SearchX } from '@lucide/vue'

defineProps<{ title: string; description?: string }>()
</script>

<template>
  <div class="empty-state">
    <span><SearchX :size="28" /></span>
    <h3>{{ title }}</h3>
    <p v-if="description">{{ description }}</p>
    <slot />
  </div>
</template>
