<script setup lang="ts">
import { Bookmark, MapPin } from '@lucide/vue'
import { ref, watch } from 'vue'
import { bookmarkLocation, unbookmarkLocation } from '@/services/locations'
import type { Location } from '@/types'

const props = withDefaults(defineProps<{
  location: Location
  showBookmark?: boolean
}>(), {
  showBookmark: true,
})

const emit = defineEmits<{
  bookmarkChanged: [payload: { contentid: string; active: boolean }]
}>()

const categoryName: Record<string, string> = {
  '12': '관광지', '14': '문화시설', '15': '축제공연행사', '25': '여행코스',
  '28': '레포츠', '32': '숙박', '38': '쇼핑', '39': '음식점',
}

const bookmarked = ref(Boolean(props.location.bookmarked))
const bookmarkLoading = ref(false)

watch(
  () => props.location.bookmarked,
  (value) => { bookmarked.value = Boolean(value) },
)

async function toggleBookmark(): Promise<void> {
  if (bookmarkLoading.value) return
  bookmarkLoading.value = true
  try {
    const result = bookmarked.value
      ? await unbookmarkLocation(props.location.contentid)
      : await bookmarkLocation(props.location.contentid)
    bookmarked.value = result.active
    emit('bookmarkChanged', { contentid: props.location.contentid, active: result.active })
  } finally {
    bookmarkLoading.value = false
  }
}
</script>

<template>
  <article class="location-card">
    <RouterLink
      :to="{ path: `/locations/${props.location.contentid}`, query: { region: props.location.region } }"
      class="location-card-link"
    >
      <div class="location-image-wrap">
        <img :src="location.firstimage || ''" :alt="location.title" loading="lazy" />
        <small>{{ location.region }}</small>
      </div>
      <div class="location-body">
        <div class="post-badges">
          <span class="category-badge">{{ categoryName[location.contenttypeid] || location.contenttypeid }}</span>
        </div>
        <h3>{{ location.title }}</h3>
        <div class="location-address"><MapPin :size="14" /> {{ location.addr1 || '주소 미제공' }}</div>
        <p class="source-mini">출처: 한국관광공사 · 공공누리 제3유형</p>
      </div>
    </RouterLink>

    <button
      v-if="showBookmark"
      type="button"
      class="location-card-bookmark"
      :class="{ selected: bookmarked }"
      :disabled="bookmarkLoading"
      :aria-label="bookmarked ? '지역정보 북마크 해제' : '지역정보 북마크 추가'"
      :title="bookmarked ? '북마크 해제' : '북마크 추가'"
      @click.stop="toggleBookmark"
    >
      <Bookmark :size="18" :fill="bookmarked ? 'currentColor' : 'none'" />
    </button>
  </article>
</template>
