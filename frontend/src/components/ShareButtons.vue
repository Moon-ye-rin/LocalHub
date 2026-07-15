<script setup lang="ts">
import { Link2, MessageCircle } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
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

const { t } = useI18n()
const message = ref('')
const sharing = ref(false)
const shareUrl = computed(() => getShareUrl(props.kind, props.resourceId))
const shareImage = computed(() => props.imageUrl || `${API_BASE_URL.replace(/\/$/, '')}/static/og-default.png`)

async function shareToKakao(): Promise<void> {
  if (sharing.value) return
  message.value = ''
  const javascriptKey = import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY?.trim()
  if (!javascriptKey) {
    message.value = t('share.keyMissing')
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
        description: (props.description || t('share.defaultDescription')).slice(0, 200),
        imageUrl: shareImage.value,
        link: { mobileWebUrl: shareUrl.value, webUrl: shareUrl.value },
      },
      social: {
        likeCount: Math.max(0, props.likeCount || 0),
        commentCount: Math.max(0, props.commentCount || 0),
      },
      buttons: [{ title: t('share.viewAtLocalHub'), link: { mobileWebUrl: shareUrl.value, webUrl: shareUrl.value } }],
    })
  } catch (error) {
    message.value = error instanceof Error ? error.message : t('share.kakaoFailed')
  } finally {
    sharing.value = false
  }
}

async function copyLink(): Promise<void> {
  message.value = ''
  try {
    await copyToClipboard(shareUrl.value)
    message.value = t('share.copied')
  } catch {
    message.value = t('share.copyFailed')
  }
}
</script>

<template>
  <div class="share-control" :aria-label="$t('share.label')">
    <button type="button" class="share-button kakao-share" :disabled="sharing" @click="shareToKakao">
      <MessageCircle :size="17" fill="currentColor" />
      {{ sharing ? $t('share.connecting') : $t('share.kakao') }}
    </button>
    <button type="button" class="share-button link-share" @click="copyLink">
      <Link2 :size="17" /> {{ $t('share.copy') }}
    </button>
    <span v-if="message" class="share-message" role="status">{{ message }}</span>
  </div>
</template>

<style scoped>
.share-control { position: relative; display: inline-flex; align-items: center; gap: 9px; }
.share-button { min-height: 42px; padding: 0 15px; display: inline-flex; align-items: center; justify-content: center; gap: 7px; border: 1px solid var(--border); border-radius: 12px; background: white; color: #554739; font-size: 12px; font-weight: 850; white-space: nowrap; cursor: pointer; transition: transform .16s ease, border-color .16s ease, background .16s ease, box-shadow .16s ease; }
.share-button:hover { transform: translateY(-1px); border-color: #d9b982; box-shadow: 0 7px 16px rgba(76,48,16,.08); }
.share-button:disabled { opacity: .62; cursor: wait; transform: none; box-shadow: none; }
.kakao-share { border-color: #f1d500; background: #fee500; color: #191919; }
.kakao-share:hover { border-color: #e4ca00; background: #f5dc00; }
.link-share:hover { background: #fff8eb; color: #9b5e00; }
.share-message { position: absolute; right: 0; top: calc(100% + 8px); z-index: 4; max-width: 310px; padding: 8px 11px; border: 1px solid #ead8bf; border-radius: 9px; background: #fffaf2; color: #7a5a31; box-shadow: 0 7px 18px rgba(75,48,17,.10); font-size: 10px; line-height: 1.45; }
@media (max-width: 720px) { .share-control { width: 100%; display: grid; grid-template-columns: 1fr 1fr; } .share-button { width: 100%; } .share-message { position: static; grid-column: 1 / -1; width: 100%; max-width: none; } }
</style>
