<script setup lang="ts">
import { ArrowLeft, Hash, ImagePlus, MapPin, Save, X } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getApiErrorMessage, resolveApiAsset } from '@/services/api'
import { createPost, deletePostImage, fetchPost, updatePost, uploadPostImage } from '@/services/posts'
import { CATEGORY_OPTIONS } from '@/types'
import { getDistrictOptions, REGION_OPTIONS, type PostRegion } from '@/constants/regions'

interface SelectedImage {
  file: File
  previewUrl: string
}

interface ExistingImage {
  storedUrl: string
  displayUrl: string
}

const route = useRoute()
const router = useRouter()
const editing = computed(() => route.name === 'post-edit')
const postId = computed(() => Number(route.params.id))
const loading = ref(false)
const initializing = ref(editing.value)
const error = ref('')
const tagInput = ref('')
const imageInput = ref<HTMLInputElement | null>(null)
const selectedImages = ref<SelectedImage[]>([])
const existingImages = ref<ExistingImage[]>([])
const deletingImageUrls = ref<string[]>([])
const form = reactive({ category: '관광지', region: '서울' as PostRegion, district: '중구', title: '', content: '', password: '', tags: [] as string[] })
const districtOptions = computed(() => getDistrictOptions(form.region))
const categories = [...CATEGORY_OPTIONS.map((item) => item.label), '자유']
const MAX_IMAGES = 5
const MAX_IMAGE_BYTES = 5 * 1024 * 1024
const ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'image/gif'])

onMounted(async () => {
  if (!editing.value) return
  const password = sessionStorage.getItem(`localhub-edit-password-${postId.value}`)
  if (!password) { await router.replace(`/posts/${postId.value}`); return }
  try {
    const post = await fetchPost(postId.value)
    form.category = post.category
    form.region = post.region || '서울'
    const allowedDistricts = getDistrictOptions(form.region)
    form.district = post.district && (allowedDistricts as readonly string[]).includes(post.district)
      ? post.district
      : allowedDistricts[0]
    form.title = post.title
    form.content = post.content
    form.password = password
    form.tags = [...post.tags]
    existingImages.value = (post.images || []).map((storedUrl) => ({ storedUrl, displayUrl: resolveApiAsset(storedUrl) }))
  } catch (caught) { error.value = getApiErrorMessage(caught, '게시글을 불러오지 못했습니다.') }
  finally { initializing.value = false }
})

onBeforeUnmount(() => {
  selectedImages.value.forEach((item) => URL.revokeObjectURL(item.previewUrl))
})

watch(() => form.region, () => {
  if (!(districtOptions.value as readonly string[]).includes(form.district)) {
    form.district = districtOptions.value[0]
  }
})

function addTag(): void {
  const tag = tagInput.value.trim().replace(/^#/, '').slice(0, 30)
  if (tag && form.tags.length < 10 && !form.tags.includes(tag)) form.tags.push(tag)
  tagInput.value = ''
}

function openImagePicker(): void {
  imageInput.value?.click()
}

function handleImageSelection(event: Event): void {
  error.value = ''
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''

  for (const file of files) {
    if (existingImages.value.length + selectedImages.value.length >= MAX_IMAGES) {
      error.value = `기존 이미지를 포함해 최대 ${MAX_IMAGES}개까지 첨부할 수 있습니다.`
      break
    }
    if (!ALLOWED_TYPES.has(file.type)) {
      error.value = 'JPG, JPEG, PNG, GIF 이미지만 첨부할 수 있습니다.'
      continue
    }
    if (file.size > MAX_IMAGE_BYTES) {
      error.value = `${file.name}: 이미지 크기는 5MB 이하여야 합니다.`
      continue
    }
    selectedImages.value.push({ file, previewUrl: URL.createObjectURL(file) })
  }
}

function removeSelectedImage(index: number): void {
  const [removed] = selectedImages.value.splice(index, 1)
  if (removed) URL.revokeObjectURL(removed.previewUrl)
}

async function removeExistingImage(image: ExistingImage, index: number): Promise<void> {
  if (!editing.value || deletingImageUrls.value.includes(image.storedUrl)) return
  if (!window.confirm('이 이미지를 게시글에서 삭제할까요? 삭제 후에는 복구할 수 없습니다.')) return

  error.value = ''
  deletingImageUrls.value.push(image.storedUrl)
  try {
    await deletePostImage(postId.value, image.storedUrl, form.password)
    existingImages.value.splice(index, 1)
  } catch (caught) {
    error.value = getApiErrorMessage(caught, '기존 이미지 삭제에 실패했습니다.')
  } finally {
    deletingImageUrls.value = deletingImageUrls.value.filter((url) => url !== image.storedUrl)
  }
}

async function submit(): Promise<void> {
  error.value = ''
  if (!form.region || !form.district) { error.value = '지역과 세부 지역을 선택해 주세요.'; return }
  if (!form.title.trim()) { error.value = '제목을 입력해 주세요.'; return }
  if (!form.content.trim()) { error.value = '내용을 입력해 주세요.'; return }
  if (form.password.length < 4) { error.value = '수정용 비밀번호는 4자 이상 입력해 주세요.'; return }

  loading.value = true
  try {
    const payload = {
      category: form.category,
      region: form.region,
      district: form.district,
      title: form.title.trim(),
      content: form.content.trim(),
      password: form.password,
      tags: form.tags,
    }
    const id = editing.value ? await updatePost(postId.value, payload) : await createPost(payload)

    const failedFiles: string[] = []
    for (const item of selectedImages.value) {
      try { await uploadPostImage(id, item.file) }
      catch { failedFiles.push(item.file.name) }
    }
    if (failedFiles.length > 0) {
      sessionStorage.setItem(
        `localhub-upload-warning-${id}`,
        `게시글은 저장됐지만 ${failedFiles.length}개 이미지 업로드에 실패했습니다: ${failedFiles.join(', ')}`,
      )
    }

    sessionStorage.removeItem(`localhub-edit-password-${id}`)
    await router.push(`/posts/${id}`)
  } catch (caught) { error.value = getApiErrorMessage(caught, '게시글 저장에 실패했습니다.') }
  finally { loading.value = false }
}
</script>

<template>
  <div class="page-container form-page">
    <RouterLink :to="editing ? `/posts/${postId}` : '/board'" class="back-link">
      <ArrowLeft :size="17" /> {{ editing ? '게시글로 돌아가기' : '게시판으로 돌아가기' }}
    </RouterLink>

    <section class="form-card">
      <header class="form-heading">
        <span class="eyebrow">COMMUNITY</span>
        <h1>{{ editing ? '게시글 수정' : '새 게시글 작성' }}</h1>
        <p>익명으로 작성되며, 비밀번호는 수정·삭제에만 사용됩니다.</p>
      </header>

      <div v-if="initializing" class="skeleton-card form-skeleton"></div>
      <form v-else class="post-form" @submit.prevent="submit">
        <div class="form-field">
          <label class="field-label">카테고리</label>
          <div class="choice-row category-choice-row">
            <button
              v-for="item in categories"
              :key="item"
              type="button"
              :class="['choice-button', { active: form.category === item }]"
              @click="form.category = item"
            >
              {{ item }}
            </button>
          </div>
        </div>


        <div class="form-field compact-region-field">
          <label class="field-label"><MapPin :size="15" /> 게시글 지역</label>
          <div class="region-dropdown-row">
            <label class="select-field">
              <span>광역 지역</span>
              <select v-model="form.region" class="form-input compact-select">
                <option v-for="item in REGION_OPTIONS" :key="item.value" :value="item.value">{{ item.label }}</option>
              </select>
            </label>
            <label class="select-field">
              <span>{{ form.region === '서울' ? '자치구' : '시·군' }}</span>
              <select v-model="form.district" class="form-input compact-select">
                <option v-for="item in districtOptions" :key="item" :value="item">
                  {{ form.region === '경기' ? `경기도 ${item}` : `서울 ${item}` }}
                </option>
              </select>
            </label>
          </div>
          <small class="help-text">대시보드의 인기 지역 순위 집계에 사용됩니다.</small>
        </div>

        <div class="form-field">
          <label class="field-label" for="title">제목</label>
          <input
            id="title"
            v-model="form.title"
            class="form-input"
            maxlength="200"
            required
            placeholder="지역정보나 후기를 입력해 주세요"
          />
          <small class="char-count">{{ form.title.length }}/200</small>
        </div>

        <div class="form-field">
          <label class="field-label" for="content">내용</label>
          <textarea
            id="content"
            v-model="form.content"
            class="form-input form-textarea"
            maxlength="20000"
            required
            rows="12"
            placeholder="구체적인 장소와 경험을 공유해 주세요."
          ></textarea>
          <small class="char-count">{{ form.content.length }}/20,000</small>
        </div>

        <div class="form-field">
          <label class="field-label">이미지 첨부</label>
          <input
            ref="imageInput"
            class="visually-hidden"
            type="file"
            accept="image/jpeg,image/png,image/gif"
            multiple
            @change="handleImageSelection"
          />
          <button type="button" class="image-upload-box" @click="openImagePicker">
            <ImagePlus :size="26" />
            <span>이미지를 선택하거나 추가하세요</span>
            <small>JPG·PNG·GIF, 파일당 5MB 이하, 기존 이미지 포함 최대 {{ MAX_IMAGES }}개</small>
          </button>

          <div v-if="existingImages.length || selectedImages.length" class="image-preview-grid">
            <article v-for="(image, index) in existingImages" :key="image.storedUrl" class="image-preview-card existing">
              <img :src="image.displayUrl" alt="기존 첨부 이미지" />
              <button
                type="button"
                :disabled="deletingImageUrls.includes(image.storedUrl)"
                :aria-label="deletingImageUrls.includes(image.storedUrl) ? '이미지 삭제 중' : '기존 첨부 이미지 삭제'"
                @click="removeExistingImage(image, index)"
              >
                <X :size="16" />
              </button>
              <span>{{ deletingImageUrls.includes(image.storedUrl) ? '삭제 중...' : '기존 이미지 · X로 삭제' }}</span>
            </article>
            <article v-for="(item, index) in selectedImages" :key="item.previewUrl" class="image-preview-card">
              <img :src="item.previewUrl" :alt="item.file.name" />
              <button type="button" aria-label="첨부 이미지 제거" @click="removeSelectedImage(index)">
                <X :size="16" />
              </button>
              <small>{{ item.file.name }}</small>
            </article>
          </div>
        </div>

        <div class="form-field">
          <label class="field-label">태그</label>
          <div class="tag-input-row">
            <div class="search-box">
              <Hash :size="17" />
              <input v-model="tagInput" maxlength="30" placeholder="태그 입력" @keydown.enter.prevent="addTag" />
            </div>
            <button type="button" class="button button-secondary" @click="addTag">추가</button>
          </div>
          <div class="tag-row editable-tags">
            <button v-for="(tag, index) in form.tags" :key="tag" type="button" class="tag" @click="form.tags.splice(index, 1)">
              #{{ tag }} ×
            </button>
          </div>
        </div>

        <div class="form-field">
          <label class="field-label" for="password">수정용 비밀번호</label>
          <input
            id="password"
            v-model="form.password"
            class="form-input"
            type="password"
            minlength="4"
            maxlength="100"
            required
            autocomplete="new-password"
            placeholder="4자 이상 입력"
          />
        </div>

        <p v-if="error" class="form-error">{{ error }}</p>
        <div class="form-actions">
          <RouterLink :to="editing ? `/posts/${postId}` : '/board'" class="button button-ghost">취소</RouterLink>
          <button type="submit" class="button button-primary button-large" :disabled="loading">
            <Save :size="18" /> {{ loading ? '저장 중...' : (editing ? '수정 완료' : '게시글 등록') }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>
