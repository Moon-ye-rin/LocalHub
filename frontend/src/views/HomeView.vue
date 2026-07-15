<script setup lang="ts">
import { ArrowRight, Database, FileText, MessageCircleMore } from '@lucide/vue'
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import HeroBanner from '@/components/HeroBanner.vue'
import LocationCard from '@/components/LocationCard.vue'
import PostCard from '@/components/PostCard.vue'
import { translateRegion } from '@/i18n-helpers'
import { fetchLocations } from '@/services/locations'
import { fetchPosts } from '@/services/posts'
import type { Location, Post } from '@/types'

type RegionOption = '서울' | '경기'

const { t } = useI18n()
const posts = ref<Post[]>([])
const locations = ref<Location[]>([])
const postsLoading = ref(true)
const locationsLoading = ref(true)
const bookmarked = ref<Set<number>>(new Set())
const selectedRegion = ref<RegionOption>('서울')
const REGION_OPTIONS: RegionOption[] = ['서울', '경기']

onMounted(async () => {
  try {
    bookmarked.value = new Set(JSON.parse(localStorage.getItem('localhub-bookmarks') || '[]'))
  } catch {
    bookmarked.value = new Set()
  }
  await Promise.all([loadPosts(), loadLocations()])
})

watch(selectedRegion, () => { void loadLocations() })

async function loadPosts(): Promise<void> {
  postsLoading.value = true
  try {
    const data = await fetchPosts({ page: 1, size: 4 })
    posts.value = data.posts
  } finally {
    postsLoading.value = false
  }
}

async function loadLocations(): Promise<void> {
  locationsLoading.value = true
  try {
    const data = await fetchLocations({ region: selectedRegion.value, page: 1, size: 4, contenttypeid: '12' })
    locations.value = data.items
  } finally {
    locationsLoading.value = false
  }
}

function toggleBookmark(postId: number): void {
  const next = new Set(bookmarked.value)
  if (next.has(postId)) next.delete(postId)
  else next.add(postId)
  bookmarked.value = next
  localStorage.setItem('localhub-bookmarks', JSON.stringify([...next]))
}
</script>

<template>
  <div class="page-container page-stack home-page">
    <HeroBanner />
    <section class="feature-strip">
      <article>
        <span><Database :size="22" /></span>
        <div><strong>{{ $t('home.publicDataTitle') }}</strong><p>{{ $t('home.publicDataDesc') }}</p></div>
      </article>
      <article>
        <span><FileText :size="22" /></span>
        <div><strong>{{ $t('home.communityTitle') }}</strong><p>{{ $t('home.communityDesc') }}</p></div>
      </article>
      <article>
        <span><MessageCircleMore :size="22" /></span>
        <div><strong>{{ $t('home.chatbotTitle') }}</strong><p>{{ $t('home.chatbotDesc') }}</p></div>
      </article>
    </section>

    <section class="content-section">
      <div class="section-heading">
        <div>
          <span class="eyebrow">PUBLIC DATA</span>
          <h2>{{ $t('home.recommend', { region: translateRegion(t, selectedRegion) }) }}</h2>
        </div>
        <div class="section-heading-actions">
          <div class="region-switch" :aria-label="$t('home.selectRegion')">
            <button
              v-for="item in REGION_OPTIONS"
              :key="item"
              type="button"
              :class="['region-switch-button', { active: selectedRegion === item }]"
              @click="selectedRegion = item"
            >
              {{ translateRegion(t, item) }}
            </button>
          </div>
          <RouterLink :to="{ path: '/locations', query: { region: selectedRegion } }" class="text-link">
            {{ $t('home.viewAll') }} <ArrowRight :size="16" />
          </RouterLink>
        </div>
      </div>
      <div v-if="locationsLoading" class="skeleton-grid"><div v-for="item in 4" :key="item" class="skeleton-card"></div></div>
      <div v-else class="location-grid compact-grid"><LocationCard v-for="location in locations" :key="location.contentid" :location="location" /></div>
    </section>

    <section class="content-section">
      <div class="section-heading">
        <div><span class="eyebrow">COMMUNITY</span><h2>{{ $t('home.recentPosts') }}</h2></div>
        <RouterLink to="/board" class="text-link">{{ $t('home.goBoard') }} <ArrowRight :size="16" /></RouterLink>
      </div>
      <div v-if="postsLoading" class="skeleton-grid"><div v-for="item in 4" :key="item" class="skeleton-card"></div></div>
      <div v-else class="post-grid">
        <PostCard v-for="post in posts" :key="post.id" :post="post" :bookmarked="bookmarked.has(post.id)" @bookmark="toggleBookmark" />
      </div>
    </section>
  </div>
</template>
