<script setup lang="ts">
import { Bookmark, MapPin } from '@lucide/vue'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { translateCategory, translateRegion } from '@/i18n-helpers'
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

const { t } = useI18n()
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
        <small>{{ translateRegion(t, location.region) }}</small>
      </div>
      <div class="location-body">
        <div class="post-badges">
          <span class="category-badge">{{ translateCategory(t, location.contenttypeid) }}</span>
        </div>
        <h3 lang="ko">{{ location.title }}</h3>
        <div class="location-address" lang="ko"><MapPin :size="14" /> {{ location.addr1 || $t('common.noAddress') }}</div>
        <p class="source-mini">{{ $t('common.source') }}</p>
      </div>
    </RouterLink>

    <button
      v-if="showBookmark"
      type="button"
      class="location-card-bookmark"
      :class="{ selected: bookmarked }"
      :disabled="bookmarkLoading"
      :aria-label="bookmarked ? $t('common.removeBookmark') : $t('common.addBookmark')"
      :title="bookmarked ? $t('common.removeBookmark') : $t('common.addBookmark')"
      @click.stop="toggleBookmark"
    >
      <Bookmark :size="18" :fill="bookmarked ? 'currentColor' : 'none'" />
    </button>
  </article>
</template>
