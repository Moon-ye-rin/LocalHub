<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import { computed } from 'vue'

const props = withDefaults(defineProps<{ current: number; total: number; groupSize?: number }>(), { groupSize: 10 })
const emit = defineEmits<{ change: [page: number] }>()

const groupStart = computed(() => Math.floor((props.current - 1) / props.groupSize) * props.groupSize + 1)
const groupEnd = computed(() => Math.min(groupStart.value + props.groupSize - 1, props.total))
const pages = computed(() => Array.from({ length: groupEnd.value - groupStart.value + 1 }, (_, index) => groupStart.value + index))
const hasPreviousGroup = computed(() => groupStart.value > 1)
const hasNextGroup = computed(() => groupEnd.value < props.total)
</script>

<template>
  <nav v-if="total > 1" class="pagination" :aria-label="$t('pagination.label')">
    <button
      type="button"
      :disabled="!hasPreviousGroup"
      :aria-label="$t('pagination.previous', { count: groupSize })"
      :title="$t('pagination.previousTitle')"
      @click="emit('change', Math.max(1, groupStart - groupSize))"
    >
      <ChevronLeft :size="17" />
    </button>
    <button
      v-for="item in pages"
      :key="item"
      type="button"
      :class="{ active: item === current }"
      @click="emit('change', item)"
    >
      {{ item }}
    </button>
    <button
      type="button"
      :disabled="!hasNextGroup"
      :aria-label="$t('pagination.next', { count: groupSize })"
      :title="$t('pagination.nextTitle')"
      @click="emit('change', Math.min(total, groupEnd + 1))"
    >
      <ChevronRight :size="17" />
    </button>
  </nav>
</template>
