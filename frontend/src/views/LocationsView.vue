<script setup lang="ts">
import { Bookmark, Database, Search } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import EmptyState from '@/components/EmptyState.vue'
import LocationCard from '@/components/LocationCard.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { translateCategory, translateRegion } from '@/i18n-helpers'
import { getApiErrorMessage } from '@/services/api'
import { fetchLocations } from '@/services/locations'
import { CATEGORY_OPTIONS, type Location } from '@/types'

type RegionOption = '전체' | '서울' | '경기'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const locations = ref<Location[]>([])
const loading = ref(true)
const error = ref('')
const search = ref(typeof route.query.q === 'string' ? route.query.q : '')
const contenttypeid = ref('')
const region = ref<RegionOption>(route.query.region === '서울' || route.query.region === '경기' ? route.query.region : '전체')
const showBookmarksOnly = ref(route.query.bookmarked === 'true')
const page = ref(1)
const totalPages = ref(0)
const total = ref(0)
const PAGE_SIZE = 21
const REGION_OPTIONS: RegionOption[] = ['전체', '서울', '경기']
let debounceTimer: number | undefined

const regionTitle = computed(() => region.value === '전체' ? t('common.seoulGyeonggi') : translateRegion(t, region.value))
const summaryLabel = computed(() => {
  if (showBookmarksOnly.value) return t('locations.bookmarkLabel', { region: regionTitle.value })
  return region.value === '전체' ? t('locations.totalLabel') : regionTitle.value
})

onMounted(loadLocations)
watch(region, async () => { page.value = 1; await syncQuery(); await loadLocations() })
watch(contenttypeid, () => { page.value = 1; void loadLocations() })
watch(search, () => {
  window.clearTimeout(debounceTimer)
  debounceTimer = window.setTimeout(() => { page.value = 1; void loadLocations() }, 300)
})

async function syncQuery(): Promise<void> {
  await router.replace({ query: { ...route.query, region: region.value, bookmarked: showBookmarksOnly.value ? 'true' : undefined } })
}

async function loadLocations(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchLocations({
      region: region.value === '전체' ? undefined : region.value,
      bookmarked_only: showBookmarksOnly.value || undefined,
      keyword: search.value || undefined,
      contenttypeid: contenttypeid.value || undefined,
      page: page.value,
      size: PAGE_SIZE,
    })
    locations.value = data.items
    total.value = data.total_count
    totalPages.value = data.total_pages
  } catch (caught) {
    error.value = getApiErrorMessage(caught, t('errors.locationsLoad'))
  } finally {
    loading.value = false
  }
}

async function toggleBookmarksOnly(): Promise<void> {
  showBookmarksOnly.value = !showBookmarksOnly.value
  page.value = 1
  await syncQuery()
  await loadLocations()
}

function handleBookmarkChanged(payload: { contentid: string; active: boolean }): void {
  const target = locations.value.find((item) => item.contentid === payload.contentid)
  if (target) target.bookmarked = payload.active
  if (showBookmarksOnly.value && !payload.active) void loadLocations()
}

function changePage(next: number): void {
  page.value = next
  void loadLocations()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <div class="page-container page-stack locations-page">
    <section class="page-title-row">
      <div>
        <span class="eyebrow">PUBLIC DATA</span>
        <h1>{{ $t('locations.title', { region: regionTitle }) }}</h1>
        <p>{{ $t('locations.description') }}</p>
        <small v-if="locale === 'en'" class="original-data-note">{{ $t('locations.originalNotice') }}</small>
      </div>
      <div class="data-badge"><Database :size="17" /> {{ $t('locations.cache') }}</div>
    </section>

    <section class="filter-panel">
      <div class="location-search-row">
        <div class="search-box">
          <Search :size="19" />
          <input v-model="search" type="search" :placeholder="$t('locations.searchPlaceholder', { region: regionTitle })" />
        </div>
        <button type="button" :class="['bookmark-filter location-bookmark-filter', { active: showBookmarksOnly }]" @click="toggleBookmarksOnly">
          <Bookmark :size="16" :fill="showBookmarksOnly ? 'currentColor' : 'none'" />
          {{ showBookmarksOnly ? $t('locations.showAll') : $t('locations.bookmarksOnly') }}
        </button>
      </div>
      <div class="filter-row">
        <div class="filter-group">
          <span>{{ $t('locations.regionSelect') }}</span>
          <button v-for="item in REGION_OPTIONS" :key="item" type="button" :class="['filter-chip', { active: region === item }]" @click="region = item">
            {{ translateRegion(t, item) }}
          </button>
        </div>
        <div class="filter-group">
          <span>{{ $t('locations.contentType') }}</span>
          <button type="button" :class="['filter-chip', { active: contenttypeid === '' }]" @click="contenttypeid = ''">{{ $t('common.all') }}</button>
          <button v-for="item in CATEGORY_OPTIONS" :key="item.code" type="button" :class="['filter-chip', { active: contenttypeid === item.code }]" @click="contenttypeid = item.code">
            {{ translateCategory(t, item.code) }}
          </button>
        </div>
      </div>
    </section>

    <div class="list-summary">{{ $t('locations.summary', { count: total.toLocaleString(), label: summaryLabel }) }}</div>
    <div v-if="loading" class="location-grid"><div v-for="item in PAGE_SIZE" :key="item" class="skeleton-card"></div></div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>
    <EmptyState
      v-else-if="locations.length === 0"
      :title="showBookmarksOnly ? $t('locations.noBookmarks') : $t('locations.notFound')"
      :description="showBookmarksOnly ? $t('locations.noBookmarksDesc') : $t('locations.notFoundDesc')"
    />
    <div v-else class="location-grid">
      <LocationCard v-for="location in locations" :key="location.contentid" :location="location" @bookmark-changed="handleBookmarkChanged" />
    </div>
    <PaginationBar :current="page" :total="totalPages" @change="changePage" />
  </div>
</template>
