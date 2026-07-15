<script setup lang="ts">
import { Bookmark, Eye, Heart, MapPin, MessageCircle, UserRound } from '@lucide/vue'
import type { Post } from '@/types'
import { formatPostRegion } from '@/constants/regions'

const props = defineProps<{ post: Post; bookmarked?: boolean }>()
const emit = defineEmits<{ bookmark: [postId: number] }>()

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('ko-KR', { month: 'short', day: 'numeric' }).format(new Date(value))
}

function handleBookmark(event: MouseEvent): void {
  event.preventDefault()
  event.stopPropagation()
  emit('bookmark', props.post.id)
}
</script>

<template>
  <RouterLink :to="`/posts/${post.id}`" class="post-card">
    <div class="post-card-top">
      <div class="post-badges">
        <span class="category-badge">{{ post.category }}</span>
        <span v-if="post.region && post.district" class="region-badge"><MapPin :size="12" /> {{ formatPostRegion(post.region, post.district) }}</span>
      </div>
      <button type="button" :class="['icon-button', { selected: bookmarked }]" @click="handleBookmark">
        <Bookmark :size="18" :fill="bookmarked ? 'currentColor' : 'none'" />
      </button>
    </div>
    <h3>{{ post.title }}</h3>
    <p class="post-excerpt">{{ post.content }}</p>
    <div class="tag-row"><span v-for="tag in post.tags.slice(0, 4)" :key="tag" class="tag">#{{ tag }}</span></div>
    <div class="post-card-footer">
      <div><strong><UserRound :size="13" /> 익명</strong><span>{{ formatDate(post.created_at) }}</span></div>
      <div class="post-metrics"><span><Eye :size="15" /> {{ post.view_count }}</span><span><Heart :size="15" /> {{ post.like_count }}</span><span><MessageCircle :size="15" /> {{ post.comment_count }}</span></div>
    </div>
  </RouterLink>
</template>
