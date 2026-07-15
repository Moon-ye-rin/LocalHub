<script setup lang="ts">
import { ArrowLeft, Bookmark, CalendarDays, Edit3, Eye, Heart, MapPin, MessageCircle, Save, Send, Trash2, UserRound, X } from '@lucide/vue'
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import PasswordModal from '@/components/PasswordModal.vue'
import ShareButtons from '@/components/ShareButtons.vue'
import { getApiErrorMessage, resolveApiAsset } from '@/services/api'
import { resetPageMeta, setPageMeta } from '@/services/share'
import { createComment, deleteComment, deletePost, fetchComments, fetchPost, likePost, unlikePost, updateComment, verifyPassword } from '@/services/posts'
import type { Comment, Post } from '@/types'
import { formatRegionLabel, localeCode, translateCategory } from '@/i18n-helpers'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const post = ref<Post | null>(null)
const comments = ref<Comment[]>([])
const loading = ref(true)
const commentsLoading = ref(true)
const error = ref('')
const uploadWarning = ref('')
const modalMode = ref<'edit' | 'delete' | null>(null)
const modalError = ref('')
const processing = ref(false)
const liked = ref(false)
const likeProcessing = ref(false)
const bookmarked = ref(false)
const postId = computed(() => Number(route.params.id))
const shareDescription = computed(() => post.value?.content.trim().replace(/\s+/g, ' ').slice(0, 160) || '')
const shareImage = computed(() => post.value?.images?.[0] ? resolveApiAsset(post.value.images[0]) : '')

const commentForm = reactive({ content: '', password: '' })
const commentSubmitting = ref(false)
const commentError = ref('')
const editingCommentId = ref<number | null>(null)
const editCommentForm = reactive({ content: '', password: '' })
const commentDeleteId = ref<number | null>(null)
const commentDeleteError = ref('')
const commentDeleting = ref(false)

onMounted(async () => {
  liked.value = readSet('localhub-liked').has(postId.value)
  bookmarked.value = readSet('localhub-bookmarks').has(postId.value)
  uploadWarning.value = sessionStorage.getItem(`localhub-upload-warning-${postId.value}`) || ''
  sessionStorage.removeItem(`localhub-upload-warning-${postId.value}`)
  try {
    post.value = await fetchPost(postId.value)
    setPageMeta({ title: `${post.value.title} | LocalHub`, description: post.value.content, image: post.value.images?.[0] ? resolveApiAsset(post.value.images[0]) : undefined, url: window.location.href })
    liked.value = Boolean(post.value.liked)
    const stored = readSet('localhub-liked')
    if (liked.value) stored.add(postId.value); else stored.delete(postId.value)
    writeSet('localhub-liked', stored)
  } catch (caught) { error.value = getApiErrorMessage(caught, t('errors.postLoad')) }
  finally { loading.value = false }
  await loadComments()
})

onUnmounted(resetPageMeta)
function readSet(key: string): Set<number> { try { return new Set(JSON.parse(localStorage.getItem(key) || '[]')) } catch { return new Set() } }
function writeSet(key: string, value: Set<number>): void { localStorage.setItem(key, JSON.stringify([...value])) }

async function handleLike(): Promise<void> {
  if (!post.value || likeProcessing.value) return
  error.value = ''; likeProcessing.value = true
  try {
    const result = liked.value ? await unlikePost(post.value.id) : await likePost(post.value.id)
    post.value.like_count = result.likeCount; liked.value = result.liked
    const stored = readSet('localhub-liked')
    if (liked.value) stored.add(post.value.id); else stored.delete(post.value.id)
    writeSet('localhub-liked', stored)
  } catch (caught) { error.value = getApiErrorMessage(caught, t('errors.like')) }
  finally { likeProcessing.value = false }
}

function toggleBookmark(): void {
  if (!post.value) return
  bookmarked.value = !bookmarked.value
  const stored = readSet('localhub-bookmarks')
  if (bookmarked.value) stored.add(post.value.id); else stored.delete(post.value.id)
  writeSet('localhub-bookmarks', stored)
}

async function confirmPassword(password: string): Promise<void> {
  if (!post.value || !modalMode.value) return
  modalError.value = ''; processing.value = true
  try {
    if (modalMode.value === 'edit') {
      await verifyPassword(post.value.id, password)
      sessionStorage.setItem(`localhub-edit-password-${post.value.id}`, password)
      modalMode.value = null
      await router.push(`/posts/${post.value.id}/edit`)
    } else {
      await deletePost(post.value.id, password)
      modalMode.value = null
      await router.push('/board')
    }
  } catch (caught) {
    modalError.value = getApiErrorMessage(caught, locale.value === 'en' ? (modalMode.value === 'edit' ? 'Password verification failed.' : 'Could not delete the post.') : (modalMode.value === 'edit' ? '비밀번호 확인에 실패했습니다.' : '삭제에 실패했습니다.'))
  } finally { processing.value = false }
}

async function loadComments(): Promise<void> {
  commentsLoading.value = true; commentError.value = ''
  try { const data = await fetchComments(postId.value); comments.value = data.comments; if (post.value) post.value.comment_count = data.total_count }
  catch (caught) { commentError.value = getApiErrorMessage(caught, t('errors.commentsLoad')) }
  finally { commentsLoading.value = false }
}

async function submitComment(): Promise<void> {
  commentError.value = ''
  if (!commentForm.content.trim()) { commentError.value = t('errors.commentRequired'); return }
  if (commentForm.password.length < 4) { commentError.value = t('errors.commentPassword'); return }
  commentSubmitting.value = true
  try { await createComment(postId.value, { content: commentForm.content.trim(), password: commentForm.password }); commentForm.content = ''; commentForm.password = ''; await loadComments() }
  catch (caught) { commentError.value = getApiErrorMessage(caught, t('errors.commentCreate')) }
  finally { commentSubmitting.value = false }
}

function beginCommentEdit(comment: Comment): void { editingCommentId.value = comment.id; editCommentForm.content = comment.content; editCommentForm.password = ''; commentError.value = '' }
function cancelCommentEdit(): void { editingCommentId.value = null; editCommentForm.content = ''; editCommentForm.password = '' }
async function saveCommentEdit(commentId: number): Promise<void> {
  commentError.value = ''
  if (!editCommentForm.content.trim()) { commentError.value = t('errors.commentEditRequired'); return }
  if (editCommentForm.password.length < 4) { commentError.value = t('errors.commentEditPassword'); return }
  try { await updateComment(postId.value, commentId, { content: editCommentForm.content.trim(), password: editCommentForm.password }); cancelCommentEdit(); await loadComments() }
  catch (caught) { commentError.value = getApiErrorMessage(caught, t('errors.commentEdit')) }
}
async function confirmCommentDelete(password: string): Promise<void> {
  if (commentDeleteId.value === null) return
  commentDeleteError.value = ''; commentDeleting.value = true
  try { await deleteComment(postId.value, commentDeleteId.value, password); commentDeleteId.value = null; await loadComments() }
  catch (caught) { commentDeleteError.value = getApiErrorMessage(caught, t('errors.commentDelete')) }
  finally { commentDeleting.value = false }
}
function formatDate(value: string): string {
  return new Intl.DateTimeFormat(localeCode(locale.value), { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}
</script>

<template>
  <div class="page-container detail-page">
    <RouterLink to="/board" class="back-link"><ArrowLeft :size="17" /> {{ $t('post.backBoard') }}</RouterLink>
    <div v-if="uploadWarning" class="alert alert-warning detail-notice">{{ uploadWarning }}</div>
    <div v-if="loading" class="detail-card skeleton-detail"></div>
    <div v-else-if="error && !post" class="alert alert-error">{{ error }}</div>

    <article v-else-if="post" class="detail-card">
      <header class="detail-header">
        <div class="post-badges">
          <span class="category-badge">{{ translateCategory(t, post.category) }}</span>
          <span v-if="post.region && post.district" class="region-badge"><MapPin :size="12" /> {{ formatRegionLabel(t, locale, post.region, post.district) }}</span>
        </div>
        <h1>{{ post.title }}</h1>
        <div class="detail-meta">
          <span><UserRound :size="15" /> {{ $t('common.anonymous') }}</span>
          <span><CalendarDays :size="15" /> {{ formatDate(post.created_at) }}</span>
          <span><Eye :size="15" /> {{ post.view_count }}</span>
          <span><MessageCircle :size="15" /> {{ post.comment_count }}</span>
        </div>
      </header>

      <div class="detail-content">{{ post.content }}</div>
      <div v-if="post.images?.length" class="post-images"><img v-for="image in post.images" :key="image" :src="resolveApiAsset(image)" :alt="$t('post.attachedImage')" /></div>
      <div class="tag-row detail-tags"><span v-for="tag in post.tags" :key="tag" class="tag">#{{ tag }}</span></div>

      <footer class="detail-actions">
        <div class="social-actions">
          <div class="reaction-button-group" :aria-label="$t('post.reactionLabel')">
            <button type="button" :class="['button button-secondary', { selected: liked }]" :disabled="likeProcessing" @click="handleLike"><Heart :size="17" :fill="liked ? 'currentColor' : 'none'" /> {{ $t('common.likes') }} {{ post.like_count }}</button>
            <button type="button" :class="['button button-secondary', { selected: bookmarked }]" @click="toggleBookmark"><Bookmark :size="17" :fill="bookmarked ? 'currentColor' : 'none'" /> {{ $t('common.bookmark') }}</button>
          </div>
          <ShareButtons kind="post" :resource-id="post.id" :title="post.title" :description="shareDescription" :image-url="shareImage" :like-count="post.like_count" :comment-count="post.comment_count" />
        </div>
        <div class="owner-actions">
          <button type="button" class="button button-ghost" @click="modalMode = 'edit'"><Edit3 :size="17" /> {{ $t('common.edit') }}</button>
          <button type="button" class="button button-danger-ghost" @click="modalMode = 'delete'"><Trash2 :size="17" /> {{ $t('common.delete') }}</button>
        </div>
      </footer>
      <p v-if="error" class="form-error action-error">{{ error }}</p>
    </article>

    <section v-if="post" class="comments-card">
      <header class="comments-heading"><div><span class="eyebrow">COMMENTS</span><h2>{{ $t('post.commentsTitle') }} <strong>{{ comments.length }}</strong></h2></div><MessageCircle :size="24" /></header>
      <form class="comment-write-form" @submit.prevent="submitComment">
        <label class="field-label" for="comment-content">{{ $t('post.writeComment') }}</label>
        <textarea id="comment-content" v-model="commentForm.content" class="form-input form-textarea comment-textarea" maxlength="1000" rows="3" :placeholder="$t('post.commentPlaceholder')"></textarea>
        <div class="comment-form-bottom">
          <div class="comment-password-field">
            <label class="visually-hidden" for="comment-password">{{ $t('post.commentPassword') }}</label>
            <input id="comment-password" v-model="commentForm.password" class="form-input" type="password" minlength="4" maxlength="100" autocomplete="new-password" :placeholder="$t('post.commentPasswordPlaceholder')" />
          </div>
          <button type="submit" class="button button-primary" :disabled="commentSubmitting"><Send :size="16" /> {{ commentSubmitting ? $t('post.submitting') : $t('post.submitComment') }}</button>
        </div>
      </form>

      <div v-if="commentsLoading" class="comment-loading">{{ $t('post.loadingComments') }}</div>
      <div v-else-if="comments.length === 0" class="comment-empty">{{ $t('post.firstComment') }}</div>
      <ol v-else class="comment-list">
        <li v-for="comment in comments" :key="comment.id" class="comment-item">
          <template v-if="editingCommentId !== comment.id">
            <div class="comment-meta"><span><UserRound :size="14" /> {{ $t('common.anonymous') }}</span><time>{{ formatDate(comment.updated_at || comment.created_at) }}</time><small v-if="comment.updated_at">{{ $t('post.edited') }}</small></div>
            <p>{{ comment.content }}</p>
            <div class="comment-actions"><button type="button" @click="beginCommentEdit(comment)"><Edit3 :size="14" /> {{ $t('common.edit') }}</button><button type="button" class="danger-text" @click="commentDeleteId = comment.id"><Trash2 :size="14" /> {{ $t('common.delete') }}</button></div>
          </template>
          <form v-else class="comment-edit-form" @submit.prevent="saveCommentEdit(comment.id)">
            <textarea v-model="editCommentForm.content" class="form-input form-textarea" rows="3" maxlength="1000"></textarea>
            <input v-model="editCommentForm.password" class="form-input" type="password" minlength="4" maxlength="100" :placeholder="$t('post.editPasswordPlaceholder')" />
            <div class="comment-edit-actions"><button type="button" class="button button-ghost" @click="cancelCommentEdit"><X :size="15" /> {{ $t('common.cancel') }}</button><button type="submit" class="button button-primary"><Save :size="15" /> {{ $t('common.save') }}</button></div>
          </form>
        </li>
      </ol>
      <p v-if="commentError" class="form-error">{{ commentError }}</p>
    </section>

    <PasswordModal
      :open="modalMode !== null"
      :title="modalMode === 'delete' ? $t('post.deletePostTitle') : $t('post.editPostTitle')"
      :description="modalMode === 'delete' ? $t('post.deletePostDesc') : $t('post.editPostDesc')"
      :confirm-text="modalMode === 'delete' ? $t('common.delete') : $t('common.confirm')"
      :danger="modalMode === 'delete'"
      :loading="processing"
      :error="modalError"
      @close="modalMode = null"
      @confirm="confirmPassword"
    />
    <PasswordModal
      :open="commentDeleteId !== null"
      :title="$t('post.deleteCommentTitle')"
      :description="$t('post.deleteCommentDesc')"
      :confirm-text="$t('common.delete')"
      :danger="true"
      :loading="commentDeleting"
      :error="commentDeleteError"
      @close="commentDeleteId = null"
      @confirm="confirmCommentDelete"
    />
  </div>
</template>
