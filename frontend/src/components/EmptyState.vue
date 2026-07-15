<script setup lang="ts">
import { SearchX } from '@lucide/vue'

defineProps<{ title: string; description: string }>()
</script>

<template>
  <div class="empty-state">
    <span><SearchX :size="26" /></span>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <slot />
  </div>
</template>
