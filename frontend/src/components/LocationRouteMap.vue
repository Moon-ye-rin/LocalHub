<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Location } from '@/types'

const props = defineProps<{
  start: Location
  destination: Location | null
  routeCoordinates: [number, number][]
}>()

type LatLng = [number, number]
type WorldPoint = { x: number; y: number }
type TileItem = {
  key: string
  url: string
  left: number
  top: number
}

const TILE_SIZE = 256
const MIN_ZOOM = 5
const MAX_ZOOM = 18
const mapElement = ref<HTMLDivElement | null>(null)
const viewportWidth = ref(800)
const viewportHeight = ref(420)
const centerLat = ref(37.5665)
const centerLon = ref(126.978)
const zoom = ref(15)
const dragging = ref(false)
const tileErrorCount = ref(0)
const tileSuccessCount = ref(0)

let resizeObserver: ResizeObserver | null = null
let dragStartX = 0
let dragStartY = 0
let dragStartCenter: WorldPoint = { x: 0, y: 0 }

const startPoint = computed<LatLng | null>(() => {
  if (props.start.mapy == null || props.start.mapx == null) return null
  return [props.start.mapy, props.start.mapx]
})

const destinationPoint = computed<LatLng | null>(() => {
  if (props.destination?.mapy == null || props.destination?.mapx == null) return null
  return [props.destination.mapy, props.destination.mapx]
})

const visiblePoints = computed<LatLng[]>(() => {
  if (props.routeCoordinates.length > 1) return props.routeCoordinates
  return [startPoint.value, destinationPoint.value].filter((point): point is LatLng => point !== null)
})

const centerWorld = computed(() => latLonToWorld(centerLat.value, centerLon.value, zoom.value))
const topLeftWorld = computed(() => ({
  x: centerWorld.value.x - viewportWidth.value / 2,
  y: centerWorld.value.y - viewportHeight.value / 2,
}))

const tiles = computed<TileItem[]>(() => {
  const scale = 2 ** zoom.value
  const minTileX = Math.floor(topLeftWorld.value.x / TILE_SIZE)
  const maxTileX = Math.floor((topLeftWorld.value.x + viewportWidth.value) / TILE_SIZE)
  const minTileY = Math.floor(topLeftWorld.value.y / TILE_SIZE)
  const maxTileY = Math.floor((topLeftWorld.value.y + viewportHeight.value) / TILE_SIZE)
  const values: TileItem[] = []

  for (let tileY = minTileY; tileY <= maxTileY; tileY += 1) {
    if (tileY < 0 || tileY >= scale) continue
    for (let tileX = minTileX; tileX <= maxTileX; tileX += 1) {
      const wrappedX = ((tileX % scale) + scale) % scale
      values.push({
        key: `${zoom.value}-${tileX}-${tileY}`,
        url: `https://${['a', 'b', 'c'][Math.abs(tileX + tileY) % 3]}.tile.openstreetmap.org/${zoom.value}/${wrappedX}/${tileY}.png`,
        left: tileX * TILE_SIZE - topLeftWorld.value.x,
        top: tileY * TILE_SIZE - topLeftWorld.value.y,
      })
    }
  }
  return values
})

const routePolyline = computed(() => (
  props.routeCoordinates
    .map(([lat, lon]) => toViewportPoint([lat, lon]))
    .map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`)
    .join(' ')
))

const startPixel = computed(() => startPoint.value ? toViewportPoint(startPoint.value) : null)
const destinationPixel = computed(() => destinationPoint.value ? toViewportPoint(destinationPoint.value) : null)

const tileLayerFailed = computed(() => (
  tiles.value.length > 0
  && tileSuccessCount.value === 0
  && tileErrorCount.value >= Math.min(4, tiles.value.length)
))

onMounted(async () => {
  await nextTick()
  updateViewportSize()
  resizeObserver = new ResizeObserver(() => {
    updateViewportSize()
  })
  if (mapElement.value) resizeObserver.observe(mapElement.value)
  fitToPoints()
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
})

watch(
  () => [props.start.contentid, props.destination?.contentid, props.routeCoordinates] as const,
  async () => {
    tileErrorCount.value = 0
    tileSuccessCount.value = 0
    await nextTick()
    fitToPoints()
  },
  { deep: true },
)

function updateViewportSize(): void {
  if (!mapElement.value) return
  const rect = mapElement.value.getBoundingClientRect()
  if (rect.width > 0) viewportWidth.value = rect.width
  if (rect.height > 0) viewportHeight.value = rect.height
}

function fitToPoints(): void {
  const points = visiblePoints.value
  if (!points.length) return
  if (points.length === 1) {
    centerLat.value = points[0][0]
    centerLon.value = points[0][1]
    zoom.value = 15
    return
  }

  const padding = Math.min(64, Math.max(34, viewportWidth.value * 0.08))
  let selectedZoom = MIN_ZOOM
  for (let candidate = MAX_ZOOM; candidate >= MIN_ZOOM; candidate -= 1) {
    const worldPoints = points.map(([lat, lon]) => latLonToWorld(lat, lon, candidate))
    const xs = worldPoints.map((point) => point.x)
    const ys = worldPoints.map((point) => point.y)
    const width = Math.max(...xs) - Math.min(...xs)
    const height = Math.max(...ys) - Math.min(...ys)
    if (width <= viewportWidth.value - padding * 2 && height <= viewportHeight.value - padding * 2) {
      selectedZoom = candidate
      break
    }
  }

  const worldPoints = points.map(([lat, lon]) => latLonToWorld(lat, lon, selectedZoom))
  const xs = worldPoints.map((point) => point.x)
  const ys = worldPoints.map((point) => point.y)
  const center = {
    x: (Math.min(...xs) + Math.max(...xs)) / 2,
    y: (Math.min(...ys) + Math.max(...ys)) / 2,
  }
  const converted = worldToLatLon(center.x, center.y, selectedZoom)
  zoom.value = selectedZoom
  centerLat.value = converted.lat
  centerLon.value = converted.lon
}

function latLonToWorld(lat: number, lon: number, targetZoom: number): WorldPoint {
  const safeLat = Math.max(-85.05112878, Math.min(85.05112878, lat))
  const scale = TILE_SIZE * 2 ** targetZoom
  const sinLat = Math.sin(safeLat * Math.PI / 180)
  return {
    x: ((lon + 180) / 360) * scale,
    y: (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) * scale,
  }
}

function worldToLatLon(x: number, y: number, targetZoom: number): { lat: number; lon: number } {
  const scale = TILE_SIZE * 2 ** targetZoom
  const lon = x / scale * 360 - 180
  const n = Math.PI - 2 * Math.PI * y / scale
  const lat = 180 / Math.PI * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)))
  return { lat, lon }
}

function toViewportPoint(point: LatLng): WorldPoint {
  const world = latLonToWorld(point[0], point[1], zoom.value)
  return {
    x: world.x - topLeftWorld.value.x,
    y: world.y - topLeftWorld.value.y,
  }
}

function changeZoom(delta: number): void {
  zoom.value = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom.value + delta))
  tileErrorCount.value = 0
  tileSuccessCount.value = 0
}

function onPointerDown(event: PointerEvent): void {
  if (event.button !== 0 || !mapElement.value) return
  dragging.value = true
  dragStartX = event.clientX
  dragStartY = event.clientY
  dragStartCenter = { ...centerWorld.value }
  mapElement.value.setPointerCapture(event.pointerId)
}

function onPointerMove(event: PointerEvent): void {
  if (!dragging.value) return
  const nextCenter = {
    x: dragStartCenter.x - (event.clientX - dragStartX),
    y: dragStartCenter.y - (event.clientY - dragStartY),
  }
  const converted = worldToLatLon(nextCenter.x, nextCenter.y, zoom.value)
  centerLat.value = converted.lat
  centerLon.value = converted.lon
}

function onPointerUp(event: PointerEvent): void {
  if (!dragging.value || !mapElement.value) return
  dragging.value = false
  if (mapElement.value.hasPointerCapture(event.pointerId)) {
    mapElement.value.releasePointerCapture(event.pointerId)
  }
}

function handleTileLoad(): void {
  tileSuccessCount.value += 1
}

function handleTileError(): void {
  tileErrorCount.value += 1
}
</script>

<template>
  <div class="route-map-wrap">
    <div
      ref="mapElement"
      :class="['embedded-map localhub-tile-map', { dragging }]"
      :aria-label="`${start.title} 경로 지도`"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    >
      <div class="localhub-map-tiles" aria-hidden="true">
        <img
          v-for="tile in tiles"
          :key="tile.key"
          :src="tile.url"
          :style="{ left: `${tile.left}px`, top: `${tile.top}px` }"
          alt=""
          draggable="false"
          @load="handleTileLoad"
          @error="handleTileError"
        />
      </div>

      <div v-if="tileLayerFailed" class="localhub-map-tile-warning">
        지도 배경을 불러오지 못했지만 출발지·도착지와 경로는 표시됩니다.
      </div>

      <svg class="localhub-map-overlay" :viewBox="`0 0 ${viewportWidth} ${viewportHeight}`" aria-hidden="true">
        <polyline
          v-if="routeCoordinates.length > 1"
          :points="routePolyline"
          class="localhub-route-shadow"
        />
        <polyline
          v-if="routeCoordinates.length > 1"
          :points="routePolyline"
          class="localhub-route-line"
        />
      </svg>

      <div
        v-if="startPixel"
        class="localhub-map-marker localhub-map-marker-start"
        :style="{ left: `${startPixel.x}px`, top: `${startPixel.y}px` }"
        :title="start.title"
      >
        <span>출발</span>
      </div>
      <div
        v-if="destinationPixel && destination"
        class="localhub-map-marker localhub-map-marker-end"
        :style="{ left: `${destinationPixel.x}px`, top: `${destinationPixel.y}px` }"
        :title="destination.title"
      >
        <span>도착</span>
      </div>

      <div class="localhub-map-controls" @pointerdown.stop>
        <button type="button" aria-label="지도 확대" :disabled="zoom >= MAX_ZOOM" @click="changeZoom(1)">+</button>
        <button type="button" aria-label="지도 축소" :disabled="zoom <= MIN_ZOOM" @click="changeZoom(-1)">−</button>
        <button type="button" class="fit" aria-label="출발지와 도착지에 지도 맞춤" @click="fitToPoints">맞춤</button>
      </div>
    </div>

    <div class="route-map-legend" aria-hidden="true">
      <span><i class="start"></i> 출발지</span>
      <span><i class="end"></i> 도착지</span>
      <span><i class="path"></i> 경로</span>
    </div>
    <p class="localhub-map-attribution">지도 데이터 © OpenStreetMap contributors</p>
  </div>
</template>
