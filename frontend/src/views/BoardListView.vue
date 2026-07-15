<script setup lang="ts">
import { Bookmark, Plus, Search, SlidersHorizontal } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import EmptyState from '@/components/EmptyState.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import PostCard from '@/components/PostCard.vue'
import { translateCategory } from '@/i18n-helpers'
import { getApiErrorMessage } from '@/services/api'
import { fetchPopularTags, fetchPosts } from '@/services/posts'
import { CATEGORY_OPTIONS, type Post } from '@/types'

const { t } = useI18n()
const posts = ref<Post[]>([])
const tags = ref<Array<{ name: string; count: number }>>([])
const loading = ref(true)
const error = ref('')
const search = ref('')
const category = ref('')
const activeTag = ref('')
const sort = ref<'latest' | 'views' | 'likes'>('latest')
const page = ref(1)
const totalPages = ref(0)
const total = ref(0)
const showBookmarksOnly = ref(false)
const bookmarked = ref<Set<number>>(new Set())
let debounceTimer: number | undefined

const sortOptions = computed(() => [
  { v: 'latest' as const, l: t('common.latest') },
  { v: 'views' as const, l: t('common.viewsSort') },
  { v: 'likes' as const, l: t('common.likesSort') },
])

onMounted(async () => { loadBookmarks(); await Promise.all([loadPosts(), loadTags()]) })
watch([category, activeTag, sort], () => { page.value = 1; void loadPosts() })
watch(search, () => {
  window.clearTimeout(debounceTimer)
  debounceTimer = window.setTimeout(() => { page.value = 1; void loadPosts() }, 350)
})

function loadBookmarks(): void {
  try { bookmarked.value = new Set(JSON.parse(localStorage.getItem('localhub-bookmarks') || '[]')) }
  catch { bookmarked.value = new Set() }
}

async function loadPosts(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const response = await fetchPosts({ page: page.value, size: 8, keyword: search.value || undefined, category: category.value || undefined, tag: activeTag.value || undefined, sort: sort.value })
    posts.value = showBookmarksOnly.value ? response.posts.filter((post) => bookmarked.value.has(post.id)) : response.posts
    totalPages.value = response.total_pages
    total.value = showBookmarksOnly.value ? posts.value.length : response.total_count
  } catch (caught) { error.value = getApiErrorMessage(caught, t('errors.postsLoad')) }
  finally { loading.value = false }
}

async function loadTags(): Promise<void> {
  try { tags.value = await fetchPopularTags() }
  catch { tags.value = [] }
}

function toggleBookmark(postId: number): void {
  const next = new Set(bookmarked.value)
  if (next.has(postId)) next.delete(postId)
  else next.add(postId)
  bookmarked.value = next
  localStorage.setItem('localhub-bookmarks', JSON.stringify([...next]))
  if (showBookmarksOnly.value) void loadPosts()
}

function toggleBookmarksOnly(): void { showBookmarksOnly.value = !showBookmarksOnly.value; page.value = 1; void loadPosts() }
function changePage(next: number): void { page.value = next; void loadPosts(); window.scrollTo({ top: 0, behavior: 'smooth' }) }
function resetFilters(): void { search.value = ''; category.value = ''; activeTag.value = ''; sort.value = 'latest'; showBookmarksOnly.value = false }
</script>

<template>
  <div class="page-container page-stack board-page">
    <section class="page-title-row">
      <div><span class="eyebrow">COMMUNITY</span><h1>{{ $t('board.title') }}</h1><p>{{ $t('board.description') }}</p></div>
      <RouterLink to="/posts/new" class="button button-primary"><Plus :size="18" /> {{ $t('common.newPost') }}</RouterLink>
    </section>

    <section class="filter-panel">
      <div class="search-box"><Search :size="19" /><input v-model="search" type="search" :placeholder="$t('board.searchPlaceholder')" /></div>
      <div class="filter-row">
        <div class="filter-group">
          <span><SlidersHorizontal :size="15" /> {{ $t('common.category') }}</span>
          <button type="button" :class="['filter-chip', { active: category === '' }]" @click="category = ''">{{ $t('common.all') }}</button>
          <button v-for="item in CATEGORY_OPTIONS" :key="item.code" type="button" :class="['filter-chip', { active: category === item.label }]" @click="category = item.label">{{ translateCategory(t, item.code) }}</button>
          <button type="button" :class="['filter-chip', { active: category === '자유' }]" @click="category = '자유'">{{ $t('categories.free') }}</button>
        </div>
        <div class="filter-group">
          <span>{{ $t('common.sort') }}</span>
          <button v-for="item in sortOptions" :key="item.v" type="button" :class="['filter-chip', { active: sort === item.v }]" @click="sort = item.v">{{ item.l }}</button>
        </div>
      </div>
      <div v-if="tags.length" class="popular-tags">
        <span>{{ $t('board.popularTags') }}</span>
        <button v-for="tagItem in tags" :key="tagItem.name" type="button" :class="['tag-filter', { active: activeTag === tagItem.name }]" @click="activeTag = activeTag === tagItem.name ? '' : tagItem.name">#{{ tagItem.name }} <small>{{ tagItem.count }}</small></button>
        <button type="button" :class="['bookmark-filter', { active: showBookmarksOnly }]" @click="toggleBookmarksOnly"><Bookmark :size="14" :fill="showBookmarksOnly ? 'currentColor' : 'none'" /> {{ $t('board.bookmarksOnly') }}</button>
      </div>
    </section>

    <div class="list-summary">{{ $t('board.summary', { count: total.toLocaleString() }) }}</div>
    <div v-if="loading" class="post-grid"><div v-for="item in 6" :key="item" class="skeleton-card post-skeleton"></div></div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>
    <EmptyState v-else-if="posts.length === 0" :title="$t('board.noResults')" :description="$t('board.noResultsDesc')"><button type="button" class="button button-secondary" @click="resetFilters">{{ $t('board.resetFilters') }}</button></EmptyState>
    <div v-else class="post-grid"><PostCard v-for="post in posts" :key="post.id" :post="post" :bookmarked="bookmarked.has(post.id)" @bookmark="toggleBookmark" /></div>
    <PaginationBar :current="page" :total="totalPages" @change="changePage" />
  </div>
</template>
