import { API_BASE_URL } from './api'

const KAKAO_SCRIPT_ID = 'localhub-kakao-sdk'
const KAKAO_SDK_URL = 'https://t1.kakaocdn.net/kakao_js_sdk/2.8.1/kakao.min.js'
const KAKAO_SDK_INTEGRITY = 'sha384-OL+ylM/iuPLtW5U3XcvLSGhE8JzReKDank5InqlHGWPhb4140/yrBw0bg0y7+C9J'

export type ShareResourceKind = 'post' | 'location'

export interface PageMeta {
  title: string
  description: string
  image?: string
  url?: string
}

export function getShareUrl(kind: ShareResourceKind, id: string | number): string {
  const collection = kind === 'post' ? 'posts' : 'locations'
  return `${API_BASE_URL.replace(/\/$/, '')}/share/${collection}/${encodeURIComponent(String(id))}`
}

export async function copyToClipboard(value: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value)
    return
  }

  const textarea = document.createElement('textarea')
  textarea.value = value
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  const copied = document.execCommand('copy')
  textarea.remove()
  if (!copied) throw new Error('클립보드 복사에 실패했습니다.')
}

export async function loadKakaoSdk(): Promise<NonNullable<Window['Kakao']>> {
  if (window.Kakao) return window.Kakao

  const existing = document.getElementById(KAKAO_SCRIPT_ID) as HTMLScriptElement | null
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener('load', () => window.Kakao ? resolve(window.Kakao) : reject(new Error('카카오 SDK를 불러오지 못했습니다.')), { once: true })
      existing.addEventListener('error', () => reject(new Error('카카오 SDK를 불러오지 못했습니다.')), { once: true })
    })
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.id = KAKAO_SCRIPT_ID
    script.src = KAKAO_SDK_URL
    script.async = true
    script.integrity = KAKAO_SDK_INTEGRITY
    script.crossOrigin = 'anonymous'
    script.addEventListener('load', () => window.Kakao ? resolve(window.Kakao) : reject(new Error('카카오 SDK 초기화에 실패했습니다.')), { once: true })
    script.addEventListener('error', () => reject(new Error('카카오 SDK를 불러오지 못했습니다.')), { once: true })
    document.head.appendChild(script)
  })
}

function setMeta(selector: string, attribute: 'name' | 'property', key: string, content: string): void {
  let element = document.head.querySelector<HTMLMetaElement>(selector)
  if (!element) {
    element = document.createElement('meta')
    element.setAttribute(attribute, key)
    document.head.appendChild(element)
  }
  element.content = content
}

function setCanonical(url: string): void {
  let canonical = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')
  if (!canonical) {
    canonical = document.createElement('link')
    canonical.rel = 'canonical'
    document.head.appendChild(canonical)
  }
  canonical.href = url
}

export function setPageMeta(meta: PageMeta): void {
  const description = meta.description.trim().slice(0, 180)
  const url = meta.url || window.location.href
  const image = meta.image || `${API_BASE_URL.replace(/\/$/, '')}/static/og-default.png`

  document.title = meta.title
  setMeta('meta[name="description"]', 'name', 'description', description)
  setMeta('meta[property="og:type"]', 'property', 'og:type', 'website')
  setMeta('meta[property="og:site_name"]', 'property', 'og:site_name', 'LocalHub')
  setMeta('meta[property="og:locale"]', 'property', 'og:locale', 'ko_KR')
  setMeta('meta[property="og:title"]', 'property', 'og:title', meta.title)
  setMeta('meta[property="og:description"]', 'property', 'og:description', description)
  setMeta('meta[property="og:image"]', 'property', 'og:image', image)
  setMeta('meta[property="og:url"]', 'property', 'og:url', url)
  setMeta('meta[name="twitter:card"]', 'name', 'twitter:card', 'summary_large_image')
  setMeta('meta[name="twitter:title"]', 'name', 'twitter:title', meta.title)
  setMeta('meta[name="twitter:description"]', 'name', 'twitter:description', description)
  setMeta('meta[name="twitter:image"]', 'name', 'twitter:image', image)
  setCanonical(url)
}

export function resetPageMeta(): void {
  const publicUrl = import.meta.env.VITE_PUBLIC_SITE_URL || window.location.origin
  setPageMeta({
    title: 'LocalHub | 서울·경기 지역정보 커뮤니티',
    description: '서울·경기 지역정보를 찾고 익명으로 후기를 공유하세요.',
    image: `${publicUrl.replace(/\/$/, '')}/og-default.png`,
    url: publicUrl,
  })
}
