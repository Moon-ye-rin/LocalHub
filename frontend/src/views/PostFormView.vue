<script setup lang="ts">
import { ArrowLeft, Hash, ImagePlus, MapPin, Save, X } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { getApiErrorMessage, resolveApiAsset } from '@/services/api'
import { createPost, deletePostImage, fetchPost, updatePost, uploadPostImage } from '@/services/posts'
import { CATEGORY_OPTIONS } from '@/types'
import { getDistrictOptions, REGION_OPTIONS, type PostRegion } from '@/constants/regions'
import { translateCategory, translateDistrict, translateRegion } from '@/i18n-helpers'

interface SelectedImage { file: File; previewUrl: string }
interface ExistingImage { storedUrl: string; displayUrl: string }

const { t, locale } = useI18n()
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
    form.district = post.district && (allowedDistricts as readonly string[]).includes(post.district) ? post.district : allowedDistricts[0]
    form.title = post.title
    form.content = post.content
    form.password = password
    form.tags = [...post.tags]
    existingImages.value = (post.images || []).map((storedUrl) => ({ storedUrl, displayUrl: resolveApiAsset(storedUrl) }))
  } catch (caught) { error.value = getApiErrorMessage(caught, t('errors.postLoad')) }
  finally { initializing.value = false }
})

onBeforeUnmount(() => { selectedImages.value.forEach((item) => URL.revokeObjectURL(item.previewUrl)) })
watch(() => form.region, () => {
  if (!(districtOptions.value as readonly string[]).includes(form.district)) form.district = districtOptions.value[0]
})

function addTag(): void {
  const tag = tagInput.value.trim().replace(/^#/, '').slice(0, 30)
  if (tag && form.tags.length < 10 && !form.tags.includes(tag)) form.tags.push(tag)
  tagInput.value = ''
}
function openImagePicker(): void { imageInput.value?.click() }
function handleImageSelection(event: Event): void {
  error.value = ''
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''
  for (const file of files) {
    if (existingImages.value.length + selectedImages.value.length >= MAX_IMAGES) {
      error.value = locale.value === 'en' ? `You can attach up to ${MAX_IMAGES} images including existing images.` : `기존 이미지를 포함해 최대 ${MAX_IMAGES}개까지 첨부할 수 있습니다.`
      break
    }
    if (!ALLOWED_TYPES.has(file.type)) {
      error.value = locale.value === 'en' ? 'Only JPG, JPEG, PNG and GIF images are supported.' : 'JPG, JPEG, PNG, GIF 이미지만 첨부할 수 있습니다.'
      continue
    }
    if (file.size > MAX_IMAGE_BYTES) {
      error.value = locale.value === 'en' ? `${file.name}: Each image must be 5 MB or smaller.` : `${file.name}: 이미지 크기는 5MB 이하여야 합니다.`
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
  if (!window.confirm(t('form.confirmImageDelete'))) return
  error.value = ''
  deletingImageUrls.value.push(image.storedUrl)
  try {
    await deletePostImage(postId.value, image.storedUrl, form.password)
    existingImages.value.splice(index, 1)
  } catch (caught) {
    error.value = getApiErrorMessage(caught, locale.value === 'en' ? 'Could not delete the existing image.' : '기존 이미지 삭제에 실패했습니다.')
  } finally {
    deletingImageUrls.value = deletingImageUrls.value.filter((url) => url !== image.storedUrl)
  }
}

async function submit(): Promise<void> {
  error.value = ''
  if (!form.region || !form.district) { error.value = t('errors.regionRequired'); return }
  if (!form.title.trim()) { error.value = t('errors.titleRequired'); return }
  if (!form.content.trim()) { error.value = t('errors.contentRequired'); return }
  if (form.password.length < 4) { error.value = t('errors.passwordMin'); return }
  loading.value = true
  try {
    const payload = { category: form.category, region: form.region, district: form.district, title: form.title.trim(), content: form.content.trim(), password: form.password, tags: form.tags }
    const id = editing.value ? await updatePost(postId.value, payload) : await createPost(payload)
    const failedFiles: string[] = []
    for (const item of selectedImages.value) {
      try { await uploadPostImage(id, item.file) }
      catch { failedFiles.push(item.file.name) }
    }
    if (failedFiles.length > 0) {
      sessionStorage.setItem(
        `localhub-upload-warning-${id}`,
        locale.value === 'en'
          ? `The post was saved, but ${failedFiles.length} image uploads failed: ${failedFiles.join(', ')}`
          : `게시글은 저장됐지만 ${failedFiles.length}개 이미지 업로드에 실패했습니다: ${failedFiles.join(', ')}`,
      )
    }
    sessionStorage.removeItem(`localhub-edit-password-${id}`)
    await router.push(`/posts/${id}`)
  } catch (caught) { error.value = getApiErrorMessage(caught, t('errors.savePost')) }
  finally { loading.value = false }
}
</script>

<template>
  <div class="page-container form-page">
    <RouterLink :to="editing ? `/posts/${postId}` : '/board'" class="back-link">
      <ArrowLeft :size="17" /> {{ editing ? $t('form.backPost') : $t('form.backBoard') }}
    </RouterLink>

    <section class="form-card">
      <header class="form-heading">
        <span class="eyebrow">COMMUNITY</span>
        <h1>{{ editing ? $t('form.editTitle') : $t('form.newTitle') }}</h1>
        <p>{{ $t('form.description') }}</p>
      </header>

      <div v-if="initializing" class="skeleton-card form-skeleton"></div>
      <form v-else class="post-form" @submit.prevent="submit">
        <div class="form-field">
          <label class="field-label">{{ $t('form.category') }}</label>
          <div class="choice-row category-choice-row">
            <button v-for="item in categories" :key="item" type="button" :class="['choice-button', { active: form.category === item }]" @click="form.category = item">
              {{ translateCategory(t, item) }}
            </button>
          </div>
        </div>

        <div class="form-field compact-region-field">
          <label class="field-label"><MapPin :size="15" /> {{ $t('form.postRegion') }}</label>
          <div class="region-dropdown-row">
            <label class="select-field">
              <span>{{ $t('form.metroRegion') }}</span>
              <select v-model="form.region" class="form-input compact-select">
                <option v-for="item in REGION_OPTIONS" :key="item.value" :value="item.value">{{ translateRegion(t, item.value) }}</option>
              </select>
            </label>
            <label class="select-field">
              <span>{{ form.region === '서울' ? $t('form.districtSeoul') : $t('form.districtGyeonggi') }}</span>
              <select v-model="form.district" class="form-input compact-select">
                <option v-for="item in districtOptions" :key="item" :value="item">{{ translateDistrict(item, locale) }}</option>
              </select>
            </label>
          </div>
          <small class="help-text">{{ $t('form.regionHelp') }}</small>
        </div>

        <div class="form-field">
          <label class="field-label" for="title">{{ $t('form.title') }}</label>
          <input id="title" v-model="form.title" class="form-input" maxlength="200" required :placeholder="$t('form.titlePlaceholder')" />
          <small class="char-count">{{ form.title.length }}/200</small>
        </div>

        <div class="form-field">
          <label class="field-label" for="content">{{ $t('form.content') }}</label>
          <textarea id="content" v-model="form.content" class="form-input form-textarea" maxlength="20000" required rows="12" :placeholder="$t('form.contentPlaceholder')"></textarea>
          <small class="char-count">{{ form.content.length }}/20,000</small>
        </div>

        <div class="form-field">
          <label class="field-label">{{ $t('form.images') }}</label>
          <input ref="imageInput" class="visually-hidden" type="file" accept="image/jpeg,image/png,image/gif" multiple @change="handleImageSelection" />
          <button type="button" class="image-upload-box" @click="openImagePicker">
            <ImagePlus :size="26" />
            <span>{{ $t('form.chooseImages') }}</span>
            <small>{{ $t('form.imageHelp', { count: MAX_IMAGES }) }}</small>
          </button>

          <div v-if="existingImages.length || selectedImages.length" class="image-preview-grid">
            <article v-for="(image, index) in existingImages" :key="image.storedUrl" class="image-preview-card existing">
              <img :src="image.displayUrl" :alt="$t('form.existingImage')" />
              <button type="button" :disabled="deletingImageUrls.includes(image.storedUrl)" :aria-label="deletingImageUrls.includes(image.storedUrl) ? $t('form.deleting') : $t('form.deleteImage')" @click="removeExistingImage(image, index)">
                <X :size="16" />
              </button>
              <span>{{ deletingImageUrls.includes(image.storedUrl) ? $t('form.deleting') : $t('form.existingDeleteHint') }}</span>
            </article>
            <article v-for="(item, index) in selectedImages" :key="item.previewUrl" class="image-preview-card">
              <img :src="item.previewUrl" :alt="item.file.name" />
              <button type="button" :aria-label="$t('form.removeImage')" @click="removeSelectedImage(index)"><X :size="16" /></button>
              <small>{{ item.file.name }}</small>
            </article>
          </div>
        </div>

        <div class="form-field">
          <label class="field-label">{{ $t('form.tags') }}</label>
          <div class="tag-input-row">
            <div class="search-box"><Hash :size="17" /><input v-model="tagInput" maxlength="30" :placeholder="$t('form.tagPlaceholder')" @keydown.enter.prevent="addTag" /></div>
            <button type="button" class="button button-secondary" @click="addTag">{{ $t('form.add') }}</button>
          </div>
          <div class="tag-row editable-tags"><button v-for="(tag, index) in form.tags" :key="tag" type="button" class="tag" @click="form.tags.splice(index, 1)">#{{ tag }} ×</button></div>
        </div>

        <div class="form-field">
          <label class="field-label" for="password">{{ $t('form.password') }}</label>
          <input id="password" v-model="form.password" class="form-input" type="password" minlength="4" maxlength="100" required autocomplete="new-password" :placeholder="$t('form.passwordPlaceholder')" />
        </div>

        <p v-if="error" class="form-error">{{ error }}</p>
        <div class="form-actions">
          <RouterLink :to="editing ? `/posts/${postId}` : '/board'" class="button button-ghost">{{ $t('common.cancel') }}</RouterLink>
          <button type="submit" class="button button-primary button-large" :disabled="loading">
            <Save :size="18" /> {{ loading ? $t('form.saveLoading') : (editing ? $t('form.editComplete') : $t('form.register')) }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>
