declare global {
  interface Window {
    L?: any
  }
}

let leafletPromise: Promise<any> | null = null

const LEAFLET_CSS_ID = 'localhub-leaflet-css'
const LEAFLET_SCRIPT_ID = 'localhub-leaflet-script'

export function loadLeaflet(): Promise<any> {
  if (window.L) return Promise.resolve(window.L)
  if (leafletPromise) return leafletPromise

  leafletPromise = new Promise((resolve, reject) => {
    if (!document.getElementById(LEAFLET_CSS_ID)) {
      const link = document.createElement('link')
      link.id = LEAFLET_CSS_ID
      link.rel = 'stylesheet'
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
      link.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY='
      link.crossOrigin = ''
      document.head.appendChild(link)
    }

    const existing = document.getElementById(LEAFLET_SCRIPT_ID) as HTMLScriptElement | null
    if (existing) {
      existing.addEventListener('load', () => resolve(window.L), { once: true })
      existing.addEventListener('error', () => reject(new Error('Leaflet을 불러오지 못했습니다.')), { once: true })
      return
    }

    const script = document.createElement('script')
    script.id = LEAFLET_SCRIPT_ID
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    script.integrity = 'sha256-20nQCchB9coqIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo='
    script.crossOrigin = ''
    script.async = true
    script.addEventListener('load', () => resolve(window.L), { once: true })
    script.addEventListener('error', () => reject(new Error('Leaflet을 불러오지 못했습니다.')), { once: true })
    document.head.appendChild(script)
  })

  return leafletPromise
}
