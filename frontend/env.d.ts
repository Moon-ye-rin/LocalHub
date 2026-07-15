/// <reference types="vite/client" />

interface KakaoShareSdk {
  sendDefault(options: Record<string, unknown>): Promise<unknown> | unknown
}

interface KakaoSdk {
  init(key: string): void
  isInitialized(): boolean
  Share: KakaoShareSdk
}

interface Window {
  Kakao?: KakaoSdk
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_PUBLIC_SITE_URL?: string
  readonly VITE_KAKAO_JAVASCRIPT_KEY?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
