<script setup lang="ts">
import { Bookmark, Database, Search } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EmptyState from '@/components/EmptyState.vue'
import LocationCard from '@/components/LocationCard.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { getApiErrorMessage } from '@/services/api'
import { fetchLocations } from '@/services/locations'
import { CATEGORY_OPTIONS, type Location } from '@/types'

type RegionOption = '전체' | '서울' | '경기'

const route = useRoute()
const router = useRouter()
const locations = ref<Location[]>([])
const loading = ref(true)
const error = ref('')
const search = ref(typeof route.query.q === 'string' ? route.query.q : '')
const contenttypeid = ref('')
const region = ref<RegionOption>(
  route.query.region === '서울' || route.query.region === '경기' ? route.query.region : '전체',
)
const showBookmarksOnly = ref(route.query.bookmarked === 'true')
const page = ref(1)
const totalPages = ref(0)
const total = ref(0)
const PAGE_SIZE = 21
const REGION_OPTIONS: RegionOption[] = ['전체', '서울', '경기']
let debounceTimer: number | undefined

const regionTitle = computed(() => region.value === '전체' ? '서울·경기' : region.value)
const summaryLabel = computed(() => {
  if (showBookmarksOnly.value) return `${regionTitle.value} 북마크`
  return region.value === '전체' ? '서울·경기 전체' : region.value
})

onMounted(loadLocations)

watch(region, async () => {
  page.value = 1
  await syncQuery()
  await loadLocations()
})
watch(contenttypeid, () => {
  page.value = 1
  void loadLocations()
})
watch(search, () => {
  window.clearTimeout(debounceTimer)
  debounceTimer = window.setTimeout(() => {
    page.value = 1
    void loadLocations()
  }, 300)
})

async function syncQuery(): Promise<void> {
  await router.replace({
    query: {
      ...route.query,
      region: region.value,
      bookmarked: showBookmarksOnly.value ? 'true' : undefined,
    },
  })
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
    error.value = getApiErrorMessage(caught, '지역정보를 불러오지 못했습니다.')
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
        <h1>{{ regionTitle }} 공공 관광정보</h1>
        <p>관광지, 문화시설, 축제, 숙박, 쇼핑과 음식점 정보를 한곳에서 찾아보세요.</p>
      </div>
      <div class="data-badge"><Database :size="17" /> 서울·경기 SQLite 캐시 연동</div>
    </section>

    <section class="filter-panel">
      <div class="location-search-row">
        <div class="search-box">
          <Search :size="19" />
          <input v-model="search" type="search" :placeholder="`${regionTitle} 장소명 또는 주소 검색`" />
        </div>
        <button
          type="button"
          :class="['bookmark-filter location-bookmark-filter', { active: showBookmarksOnly }]"
          @click="toggleBookmarksOnly"
        >
          <Bookmark :size="16" :fill="showBookmarksOnly ? 'currentColor' : 'none'" />
          {{ showBookmarksOnly ? '전체 목록 보기' : '북마크만 보기' }}
        </button>
      </div>
      <div class="filter-row">
        <div class="filter-group">
          <span>지역 선택</span>
          <button
            v-for="item in REGION_OPTIONS"
            :key="item"
            type="button"
            :class="['filter-chip', { active: region === item }]"
            @click="region = item"
          >
            {{ item }}
          </button>
        </div>
        <div class="filter-group">
          <span>콘텐츠 유형</span>
          <button type="button" :class="['filter-chip', { active: contenttypeid === '' }]" @click="contenttypeid = ''">전체</button>
          <button
            v-for="item in CATEGORY_OPTIONS"
            :key="item.code"
            type="button"
            :class="['filter-chip', { active: contenttypeid === item.code }]"
            @click="contenttypeid = item.code"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
    </section>

    <div class="list-summary">
      <strong>{{ total.toLocaleString() }}</strong>개의 {{ summaryLabel }} 지역정보
    </div>
    <div v-if="loading" class="location-grid">
      <div v-for="item in 9" :key="item" class="skeleton-card location-skeleton"></div>
    </div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>
    <EmptyState
      v-else-if="locations.length === 0"
      :title="showBookmarksOnly ? '북마크한 지역정보가 없습니다' : '지역정보를 찾지 못했습니다'"
      :description="showBookmarksOnly ? '관심 있는 지역정보 카드의 북마크 버튼을 눌러 저장해 보세요.' : '지역, 검색어 또는 콘텐츠 유형을 변경해 보세요.'"
    />
    <div v-else class="location-grid">
      <LocationCard
        v-for="location in locations"
        :key="location.contentid"
        :location="location"
        @bookmark-changed="handleBookmarkChanged"
      />
    </div>
    <PaginationBar :current="page" :total="totalPages" @change="changePage" />
  </div>
</template>
