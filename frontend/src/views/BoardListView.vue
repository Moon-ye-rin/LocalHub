<script setup lang="ts">
import { Bookmark, Plus, Search, SlidersHorizontal } from '@lucide/vue'
import { onMounted, ref, watch } from 'vue'
import EmptyState from '@/components/EmptyState.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import PostCard from '@/components/PostCard.vue'
import { getApiErrorMessage } from '@/services/api'
import { fetchPopularTags, fetchPosts } from '@/services/posts'
import { CATEGORY_OPTIONS, type Post } from '@/types'

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
    const response = await fetchPosts({
      page: page.value,
      size: 8,
      keyword: search.value || undefined,
      category: category.value || undefined,
      tag: activeTag.value || undefined,
      sort: sort.value,
    })
    posts.value = showBookmarksOnly.value ? response.posts.filter((post) => bookmarked.value.has(post.id)) : response.posts
    totalPages.value = response.total_pages
    total.value = showBookmarksOnly.value ? posts.value.length : response.total_count
  } catch (caught) { error.value = getApiErrorMessage(caught, '게시글 목록을 불러오지 못했습니다.') }
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
      <div><span class="eyebrow">COMMUNITY</span><h1>서울·경기 익명 게시판</h1><p>회원가입 없이 지역의 발견과 후기를 자유롭게 공유해 보세요.</p></div>
      <RouterLink to="/posts/new" class="button button-primary"><Plus :size="18" /> 새 글 작성</RouterLink>
    </section>

    <section class="filter-panel">
      <div class="search-box"><Search :size="19" /><input v-model="search" type="search" placeholder="제목 또는 내용 검색" /></div>
      <div class="filter-row">
        <div class="filter-group"><span><SlidersHorizontal :size="15" /> 카테고리</span><button type="button" :class="['filter-chip', { active: category === '' }]" @click="category = ''">전체</button><button v-for="item in CATEGORY_OPTIONS" :key="item.code" type="button" :class="['filter-chip', { active: category === item.label }]" @click="category = item.label">{{ item.label }}</button><button type="button" :class="['filter-chip', { active: category === '자유' }]" @click="category = '자유'">자유</button></div>
        <div class="filter-group"><span>정렬</span><button v-for="item in [{v:'latest',l:'최신순'},{v:'views',l:'조회순'},{v:'likes',l:'좋아요순'}]" :key="item.v" type="button" :class="['filter-chip', { active: sort === item.v }]" @click="sort = item.v as typeof sort">{{ item.l }}</button></div>
      </div>
      <div v-if="tags.length" class="popular-tags"><span>인기 태그</span><button v-for="tagItem in tags" :key="tagItem.name" type="button" :class="['tag-filter', { active: activeTag === tagItem.name }]" @click="activeTag = activeTag === tagItem.name ? '' : tagItem.name">#{{ tagItem.name }} <small>{{ tagItem.count }}</small></button><button type="button" :class="['bookmark-filter', { active: showBookmarksOnly }]" @click="toggleBookmarksOnly"><Bookmark :size="14" :fill="showBookmarksOnly ? 'currentColor' : 'none'" /> 북마크</button></div>
    </section>

    <div class="list-summary"><strong>{{ total }}</strong>개의 게시글</div>
    <div v-if="loading" class="post-grid"><div v-for="item in 6" :key="item" class="skeleton-card post-skeleton"></div></div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>
    <EmptyState v-else-if="posts.length === 0" title="검색 결과가 없습니다" description="검색어나 필터를 바꾸거나 첫 게시글을 작성해 보세요."><button type="button" class="button button-secondary" @click="resetFilters">필터 초기화</button></EmptyState>
    <div v-else class="post-grid"><PostCard v-for="post in posts" :key="post.id" :post="post" :bookmarked="bookmarked.has(post.id)" @bookmark="toggleBookmark" /></div>
    <PaginationBar :current="page" :total="totalPages" @change="changePage" />
  </div>
</template>
