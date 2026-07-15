<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import { computed } from 'vue'

const props = withDefaults(defineProps<{ current: number; total: number; groupSize?: number }>(), {
  groupSize: 10,
})
const emit = defineEmits<{ change: [page: number] }>()

const groupStart = computed(() => Math.floor((Math.max(props.current, 1) - 1) / props.groupSize) * props.groupSize + 1)
const groupEnd = computed(() => Math.min(groupStart.value + props.groupSize - 1, props.total))
const pages = computed(() => Array.from({ length: Math.max(groupEnd.value - groupStart.value + 1, 0) }, (_, index) => groupStart.value + index))

function go(page: number): void {
  if (page >= 1 && page <= props.total && page !== props.current) emit('change', page)
}

function previousGroup(): void {
  go(Math.max(1, groupStart.value - 1))
}

function nextGroup(): void {
  go(Math.min(props.total, groupEnd.value + 1))
}
</script>

<template>
  <nav v-if="total > 1" class="pagination" aria-label="페이지 이동">
    <button
      type="button"
      :disabled="groupStart <= 1"
      :aria-label="`이전 ${groupSize}개 페이지`"
      title="이전 페이지 묶음"
      @click="previousGroup"
    >
      <ChevronLeft :size="18" />
    </button>
    <button
      v-for="pageNumber in pages"
      :key="pageNumber"
      type="button"
      :class="{ active: pageNumber === current }"
      :aria-current="pageNumber === current ? 'page' : undefined"
      @click="go(pageNumber)"
    >
      {{ pageNumber }}
    </button>
    <button
      type="button"
      :disabled="groupEnd >= total"
      :aria-label="`다음 ${groupSize}개 페이지`"
      title="다음 페이지 묶음"
      @click="nextGroup"
    >
      <ChevronRight :size="18" />
    </button>
  </nav>
</template>
