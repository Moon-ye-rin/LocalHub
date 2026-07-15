<script setup lang="ts">
import {
  ArrowLeft,
  Bookmark,
  CalendarDays,
  Edit3,
  Eye,
  Heart,
  MapPin,
  MessageCircle,
  Save,
  Send,
  Trash2,
  UserRound,
  X,
} from '@lucide/vue'
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PasswordModal from '@/components/PasswordModal.vue'
import ShareButtons from '@/components/ShareButtons.vue'
import { getApiErrorMessage, resolveApiAsset } from '@/services/api'
import { resetPageMeta, setPageMeta } from '@/services/share'
import {
  createComment,
  deleteComment,
  deletePost,
  fetchComments,
  fetchPost,
  likePost,
  unlikePost,
  updateComment,
  verifyPassword,
} from '@/services/posts'
import type { Comment, Post } from '@/types'
import { formatPostRegion } from '@/constants/regions'

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
    setPageMeta({
      title: `${post.value.title} | LocalHub`,
      description: post.value.content,
      image: post.value.images?.[0] ? resolveApiAsset(post.value.images[0]) : undefined,
      url: window.location.href,
    })
    liked.value = Boolean(post.value.liked)
    const stored = readSet('localhub-liked')
    if (liked.value) stored.add(postId.value)
    else stored.delete(postId.value)
    writeSet('localhub-liked', stored)
  }
  catch (caught) { error.value = getApiErrorMessage(caught, '게시글을 불러오지 못했습니다.') }
  finally { loading.value = false }

  await loadComments()
})

onUnmounted(resetPageMeta)

function readSet(key: string): Set<number> {
  try { return new Set(JSON.parse(localStorage.getItem(key) || '[]')) }
  catch { return new Set() }
}

function writeSet(key: string, value: Set<number>): void {
  localStorage.setItem(key, JSON.stringify([...value]))
}

async function handleLike(): Promise<void> {
  if (!post.value || likeProcessing.value) return
  error.value = ''
  likeProcessing.value = true
  try {
    const result = liked.value
      ? await unlikePost(post.value.id)
      : await likePost(post.value.id)
    post.value.like_count = result.likeCount
    liked.value = result.liked
    const stored = readSet('localhub-liked')
    if (liked.value) stored.add(post.value.id)
    else stored.delete(post.value.id)
    writeSet('localhub-liked', stored)
  } catch (caught) {
    error.value = getApiErrorMessage(caught, '좋아요 처리에 실패했습니다.')
  } finally {
    likeProcessing.value = false
  }
}

function toggleBookmark(): void {
  if (!post.value) return
  bookmarked.value = !bookmarked.value
  const stored = readSet('localhub-bookmarks')
  if (bookmarked.value) stored.add(post.value.id)
  else stored.delete(post.value.id)
  writeSet('localhub-bookmarks', stored)
}

async function confirmPassword(password: string): Promise<void> {
  if (!post.value || !modalMode.value) return
  modalError.value = ''
  processing.value = true
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
    modalError.value = getApiErrorMessage(caught, modalMode.value === 'edit' ? '비밀번호 확인에 실패했습니다.' : '삭제에 실패했습니다.')
  } finally { processing.value = false }
}

async function loadComments(): Promise<void> {
  commentsLoading.value = true
  commentError.value = ''
  try {
    const data = await fetchComments(postId.value)
    comments.value = data.comments
    if (post.value) post.value.comment_count = data.total_count
  } catch (caught) { commentError.value = getApiErrorMessage(caught, '댓글을 불러오지 못했습니다.') }
  finally { commentsLoading.value = false }
}

async function submitComment(): Promise<void> {
  commentError.value = ''
  if (!commentForm.content.trim()) { commentError.value = '댓글 내용을 입력해 주세요.'; return }
  if (commentForm.password.length < 4) { commentError.value = '댓글 비밀번호는 4자 이상 입력해 주세요.'; return }

  commentSubmitting.value = true
  try {
    await createComment(postId.value, {
      content: commentForm.content.trim(),
      password: commentForm.password,
    })
    commentForm.content = ''
    commentForm.password = ''
    await loadComments()
  } catch (caught) { commentError.value = getApiErrorMessage(caught, '댓글 등록에 실패했습니다.') }
  finally { commentSubmitting.value = false }
}

function beginCommentEdit(comment: Comment): void {
  editingCommentId.value = comment.id
  editCommentForm.content = comment.content
  editCommentForm.password = ''
  commentError.value = ''
}

function cancelCommentEdit(): void {
  editingCommentId.value = null
  editCommentForm.content = ''
  editCommentForm.password = ''
}

async function saveCommentEdit(commentId: number): Promise<void> {
  commentError.value = ''
  if (!editCommentForm.content.trim()) { commentError.value = '수정할 댓글 내용을 입력해 주세요.'; return }
  if (editCommentForm.password.length < 4) { commentError.value = '댓글 작성 시 사용한 비밀번호를 입력해 주세요.'; return }

  try {
    await updateComment(postId.value, commentId, {
      content: editCommentForm.content.trim(),
      password: editCommentForm.password,
    })
    cancelCommentEdit()
    await loadComments()
  } catch (caught) { commentError.value = getApiErrorMessage(caught, '댓글 수정에 실패했습니다.') }
}

async function confirmCommentDelete(password: string): Promise<void> {
  if (commentDeleteId.value === null) return
  commentDeleteError.value = ''
  commentDeleting.value = true
  try {
    await deleteComment(postId.value, commentDeleteId.value, password)
    commentDeleteId.value = null
    await loadComments()
  } catch (caught) { commentDeleteError.value = getApiErrorMessage(caught, '댓글 삭제에 실패했습니다.') }
  finally { commentDeleting.value = false }
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <div class="page-container detail-page">
    <RouterLink to="/board" class="back-link"><ArrowLeft :size="17" /> 목록으로 돌아가기</RouterLink>
    <div v-if="uploadWarning" class="alert alert-warning detail-notice">{{ uploadWarning }}</div>
    <div v-if="loading" class="detail-card skeleton-detail"></div>
    <div v-else-if="error && !post" class="alert alert-error">{{ error }}</div>

    <article v-else-if="post" class="detail-card">
      <header class="detail-header">
        <div class="post-badges">
          <span class="category-badge">{{ post.category }}</span>
          <span v-if="post.region && post.district" class="region-badge"><MapPin :size="12" /> {{ formatPostRegion(post.region, post.district) }}</span>
        </div>
        <h1>{{ post.title }}</h1>
        <div class="detail-meta">
          <span><UserRound :size="15" /> 익명</span>
          <span><CalendarDays :size="15" /> {{ formatDate(post.created_at) }}</span>
          <span><Eye :size="15" /> {{ post.view_count }}</span>
          <span><MessageCircle :size="15" /> {{ post.comment_count }}</span>
        </div>
      </header>

      <div class="detail-content">{{ post.content }}</div>
      <div v-if="post.images?.length" class="post-images">
        <img v-for="image in post.images" :key="image" :src="resolveApiAsset(image)" alt="게시글 첨부 이미지" />
      </div>
      <div class="tag-row detail-tags"><span v-for="tag in post.tags" :key="tag" class="tag">#{{ tag }}</span></div>

      <footer class="detail-actions">
        <div class="social-actions">
          <div class="reaction-button-group" aria-label="게시글 반응">
            <button type="button" :class="['button button-secondary', { selected: liked }]" :disabled="likeProcessing" @click="handleLike">
              <Heart :size="17" :fill="liked ? 'currentColor' : 'none'" /> 좋아요 {{ post.like_count }}
            </button>
            <button type="button" :class="['button button-secondary', { selected: bookmarked }]" @click="toggleBookmark">
              <Bookmark :size="17" :fill="bookmarked ? 'currentColor' : 'none'" /> 북마크
            </button>
          </div>
          <ShareButtons
            kind="post"
            :resource-id="post.id"
            :title="post.title"
            :description="shareDescription"
            :image-url="shareImage"
            :like-count="post.like_count"
            :comment-count="post.comment_count"
          />
        </div>
        <div class="owner-actions">
          <button type="button" class="button button-ghost" @click="modalMode = 'edit'"><Edit3 :size="17" /> 수정</button>
          <button type="button" class="button button-danger-ghost" @click="modalMode = 'delete'"><Trash2 :size="17" /> 삭제</button>
        </div>
      </footer>
      <p v-if="error" class="form-error action-error">{{ error }}</p>
    </article>

    <section v-if="post" class="comments-card">
      <header class="comments-heading">
        <div>
          <span class="eyebrow">COMMENTS</span>
          <h2>댓글 <strong>{{ comments.length }}</strong></h2>
        </div>
        <MessageCircle :size="24" />
      </header>

      <form class="comment-write-form" @submit.prevent="submitComment">
        <label class="field-label" for="comment-content">댓글 작성</label>
        <textarea
          id="comment-content"
          v-model="commentForm.content"
          class="form-input form-textarea comment-textarea"
          maxlength="1000"
          rows="3"
          placeholder="지역정보에 대한 의견이나 추가 정보를 남겨 주세요."
        ></textarea>
        <div class="comment-form-bottom">
          <div class="comment-password-field">
            <label class="visually-hidden" for="comment-password">댓글 비밀번호</label>
            <input
              id="comment-password"
              v-model="commentForm.password"
              class="form-input"
              type="password"
              minlength="4"
              maxlength="100"
              autocomplete="new-password"
              placeholder="수정·삭제용 비밀번호(4자 이상)"
            />
          </div>
          <button type="submit" class="button button-primary" :disabled="commentSubmitting">
            <Send :size="16" /> {{ commentSubmitting ? '등록 중...' : '댓글 등록' }}
          </button>
        </div>
      </form>

      <div v-if="commentsLoading" class="comment-loading">댓글을 불러오는 중입니다.</div>
      <div v-else-if="comments.length === 0" class="comment-empty">첫 댓글을 남겨 보세요.</div>
      <ol v-else class="comment-list">
        <li v-for="comment in comments" :key="comment.id" class="comment-item">
          <template v-if="editingCommentId !== comment.id">
            <div class="comment-meta">
              <span><UserRound :size="14" /> 익명</span>
              <time>{{ formatDate(comment.updated_at || comment.created_at) }}</time>
              <small v-if="comment.updated_at">수정됨</small>
            </div>
            <p>{{ comment.content }}</p>
            <div class="comment-actions">
              <button type="button" @click="beginCommentEdit(comment)"><Edit3 :size="14" /> 수정</button>
              <button type="button" class="danger-text" @click="commentDeleteId = comment.id"><Trash2 :size="14" /> 삭제</button>
            </div>
          </template>

          <form v-else class="comment-edit-form" @submit.prevent="saveCommentEdit(comment.id)">
            <textarea v-model="editCommentForm.content" class="form-input form-textarea" rows="3" maxlength="1000"></textarea>
            <input
              v-model="editCommentForm.password"
              class="form-input"
              type="password"
              minlength="4"
              maxlength="100"
              placeholder="작성 시 비밀번호"
            />
            <div class="comment-edit-actions">
              <button type="button" class="button button-ghost" @click="cancelCommentEdit"><X :size="15" /> 취소</button>
              <button type="submit" class="button button-primary"><Save :size="15" /> 저장</button>
            </div>
          </form>
        </li>
      </ol>
      <p v-if="commentError" class="form-error">{{ commentError }}</p>
    </section>

    <PasswordModal
      :open="modalMode !== null"
      :title="modalMode === 'delete' ? '게시글 삭제' : '게시글 수정'"
      :description="modalMode === 'delete' ? '작성 시 등록한 비밀번호를 입력하면 게시글이 삭제됩니다.' : '작성 시 등록한 비밀번호를 입력하면 수정 화면으로 이동합니다.'"
      :confirm-text="modalMode === 'delete' ? '삭제' : '확인'"
      :danger="modalMode === 'delete'"
      :loading="processing"
      :error="modalError"
      @close="modalMode = null"
      @confirm="confirmPassword"
    />

    <PasswordModal
      :open="commentDeleteId !== null"
      title="댓글 삭제"
      description="댓글 작성 시 등록한 비밀번호를 입력해 주세요."
      confirm-text="삭제"
      :danger="true"
      :loading="commentDeleting"
      :error="commentDeleteError"
      @close="commentDeleteId = null"
      @confirm="confirmCommentDelete"
    />
  </div>
</template>
