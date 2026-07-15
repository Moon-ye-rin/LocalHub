<script setup lang="ts">
import { Link2, MessageCircle } from '@lucide/vue'
import { computed, ref } from 'vue'
import { API_BASE_URL } from '@/services/api'
import { copyToClipboard, getShareUrl, loadKakaoSdk, type ShareResourceKind } from '@/services/share'

const props = withDefaults(defineProps<{
  kind: ShareResourceKind
  resourceId: string | number
  title: string
  description?: string
  imageUrl?: string
  likeCount?: number
  commentCount?: number
}>(), {
  description: '',
  imageUrl: '',
  likeCount: 0,
  commentCount: 0,
})

const message = ref('')
const sharing = ref(false)
const shareUrl = computed(() => getShareUrl(props.kind, props.resourceId))
const shareImage = computed(() => props.imageUrl || `${API_BASE_URL.replace(/\/$/, '')}/static/og-default.png`)

async function shareToKakao(): Promise<void> {
  if (sharing.value) return
  message.value = ''
  const javascriptKey = import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY?.trim()
  if (!javascriptKey) {
    message.value = '카카오 JavaScript 키를 frontend/.env에 설정해 주세요.'
    return
  }

  sharing.value = true
  try {
    const Kakao = await loadKakaoSdk()
    if (!Kakao.isInitialized()) Kakao.init(javascriptKey)

    await Kakao.Share.sendDefault({
      objectType: 'feed',
      content: {
        title: props.title.slice(0, 200),
        description: (props.description || 'LocalHub에서 지역정보를 확인해 보세요.').slice(0, 200),
        imageUrl: shareImage.value,
        link: {
          mobileWebUrl: shareUrl.value,
          webUrl: shareUrl.value,
        },
      },
      social: {
        likeCount: Math.max(0, props.likeCount || 0),
        commentCount: Math.max(0, props.commentCount || 0),
      },
      buttons: [
        {
          title: 'LocalHub에서 보기',
          link: {
            mobileWebUrl: shareUrl.value,
            webUrl: shareUrl.value,
          },
        },
      ],
    })
  } catch (error) {
    message.value = error instanceof Error ? error.message : '카카오톡 공유에 실패했습니다.'
  } finally {
    sharing.value = false
  }
}

async function copyLink(): Promise<void> {
  message.value = ''
  try {
    await copyToClipboard(shareUrl.value)
    message.value = '공유 링크를 복사했습니다.'
  } catch {
    message.value = '링크 복사에 실패했습니다.'
  }
}
</script>

<template>
  <div class="share-control" aria-label="소셜 공유">
    <button type="button" class="share-button kakao-share" :disabled="sharing" @click="shareToKakao">
      <MessageCircle :size="17" fill="currentColor" />
      {{ sharing ? '연결 중' : '카카오톡 공유' }}
    </button>
    <button type="button" class="share-button link-share" @click="copyLink">
      <Link2 :size="17" /> 링크 복사
    </button>
    <span v-if="message" class="share-message" role="status">{{ message }}</span>
  </div>
</template>

<style scoped>
.share-control {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 9px;
}
.share-button {
  min-height: 42px;
  padding: 0 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: white;
  color: #554739;
  font-size: 12px;
  font-weight: 850;
  white-space: nowrap;
  cursor: pointer;
  transition: transform .16s ease, border-color .16s ease, background .16s ease, box-shadow .16s ease;
}
.share-button:hover {
  transform: translateY(-1px);
  border-color: #d9b982;
  box-shadow: 0 7px 16px rgba(76, 48, 16, .08);
}
.share-button:disabled { opacity: .62; cursor: wait; transform: none; box-shadow: none; }
.kakao-share { border-color: #f1d500; background: #fee500; color: #191919; }
.kakao-share:hover { border-color: #e4ca00; background: #f5dc00; }
.link-share:hover { background: #fff8eb; color: #9b5e00; }
.share-message {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  z-index: 4;
  max-width: 310px;
  padding: 8px 11px;
  border: 1px solid #ead8bf;
  border-radius: 9px;
  background: #fffaf2;
  color: #7a5a31;
  box-shadow: 0 7px 18px rgba(75, 48, 17, .10);
  font-size: 10px;
  line-height: 1.45;
}
@media (max-width: 720px) {
  .share-control { width: 100%; display: grid; grid-template-columns: 1fr 1fr; }
  .share-button { width: 100%; }
  .share-message { position: static; grid-column: 1 / -1; width: 100%; max-width: none; }
}
</style>
