<script setup lang="ts">
import {
  ArrowLeft,
  Bookmark,
  Car,
  Edit3,
  Footprints,
  Eye,
  Heart,
  LoaderCircle,
  MapPin,
  Navigation,
  Route as RouteIcon,
  Search,
  MessageCircle,
  Phone,
  Save,
  Send,
  Star,
  Trash2,
  UserRound,
  X,
} from '@lucide/vue'
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import LocationCard from '@/components/LocationCard.vue'
import LocationRouteMap from '@/components/LocationRouteMap.vue'
import PasswordModal from '@/components/PasswordModal.vue'
import ShareButtons from '@/components/ShareButtons.vue'
import { getApiErrorMessage } from '@/services/api'
import { resetPageMeta, setPageMeta } from '@/services/share'
import {
  bookmarkLocation,
  createLocationComment,
  deleteLocationComment,
  fetchLocation,
  fetchLocationComments,
  fetchLocations,
  likeLocation,
  unbookmarkLocation,
  unlikeLocation,
  updateLocationComment,
} from '@/services/locations'
import { fetchAStarRoute } from '@/services/routes'
import {
  CATEGORY_OPTIONS,
  type AStarRouteData,
  type Location,
  type LocationComment,
} from '@/types'

const route = useRoute()
const location = ref<Location | null>(null)
const comments = ref<LocationComment[]>([])
const loading = ref(true)
const commentsLoading = ref(true)
const error = ref('')
const actionError = ref('')
const reactionProcessing = ref(false)
const commentSubmitting = ref(false)
const commentError = ref('')
const editCommentError = ref('')
const editingCommentId = ref<number | null>(null)
const commentUpdating = ref(false)
const commentDeleteId = ref<number | null>(null)
const commentDeleting = ref(false)
const commentDeleteError = ref('')
const commentForm = reactive({ nickname: '', content: '', rating: 0, password: '' })
const editForm = reactive({ nickname: '', content: '', rating: 0, password: '' })

const destinationKeyword = ref('')
const destinationRegion = ref<'전체' | '서울' | '경기'>('전체')
const destinationResults = ref<Location[]>([])
const destination = ref<Location | null>(null)
const destinationSearching = ref(false)
const destinationSearchOpen = ref(false)
const mapView = ref<'location' | 'route'>('location')
const routeData = ref<AStarRouteData | null>(null)
const routeLoading = ref(false)
const routeError = ref('')
let destinationSearchTimer: number | undefined

const contentid = computed(() => String(route.params.contentid))
const categoryName = computed(() => CATEGORY_OPTIONS.find((item) => item.code === location.value?.contenttypeid)?.label || location.value?.contenttypeid)
const shareDescription = computed(() => [location.value?.region, categoryName.value, location.value?.addr1].filter(Boolean).join(' · '))

const mapEmbedUrl = computed(() => {
  const longitude = location.value?.mapx
  const latitude = location.value?.mapy
  if (longitude == null || latitude == null) return ''
  const longitudeDelta = 0.008
  const latitudeDelta = 0.005
  const params = new URLSearchParams({
    bbox: [
      longitude - longitudeDelta,
      latitude - latitudeDelta,
      longitude + longitudeDelta,
      latitude + latitudeDelta,
    ].join(','),
    layer: 'mapnik',
    marker: `${latitude},${longitude}`,
  })
  return `https://www.openstreetmap.org/export/embed.html?${params.toString()}`
})

const routeCoordinates = computed<[number, number][]>(() => routeData.value?.coordinates || [])
const routeDriveMinutes = computed(() => {
  if (!routeData.value) return 0
  return routeData.value.drive_minutes ?? Math.max(1, Math.round((routeData.value.distance_m / 1000) / 30 * 60))
})
const routeWalkMinutes = computed(() => {
  if (!routeData.value) return 0
  return routeData.value.walk_minutes ?? Math.max(1, Math.round((routeData.value.distance_m / 1000) / 4.5 * 60))
})


watch(contentid, () => {
  void loadPage()
}, { immediate: true })

watch(destinationKeyword, (value) => {
  if (destination.value && value !== destination.value.title) {
    destination.value = null
    routeData.value = null
  }
  if (destinationSearchTimer) window.clearTimeout(destinationSearchTimer)
  const keyword = value.trim()
  if (!keyword || destination.value?.title === keyword) {
    destinationResults.value = []
    destinationSearchOpen.value = false
    return
  }
  destinationSearchTimer = window.setTimeout(() => {
    void searchDestinations()
  }, 280)
})

watch(destinationRegion, () => {
  destination.value = null
  routeData.value = null
  if (destinationKeyword.value.trim()) void searchDestinations()
})

onUnmounted(() => {
  resetPageMeta()
  if (destinationSearchTimer) window.clearTimeout(destinationSearchTimer)
})

async function loadPage(): Promise<void> {
  loading.value = true
  error.value = ''
  actionError.value = ''
  comments.value = []
  mapView.value = 'location'
  resetRoutePlanner()
  cancelCommentEdit()
  try {
    location.value = await fetchLocation(contentid.value)
    setPageMeta({
      title: `${location.value.title} | LocalHub`,
      description: shareDescription.value,
      image: location.value.firstimage || undefined,
      url: window.location.href,
    })
    await loadComments()
    await autoRouteFromQuery()
  } catch (caught) {
    error.value = getApiErrorMessage(caught, '지역정보를 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
}

async function loadComments(): Promise<void> {
  commentsLoading.value = true
  commentError.value = ''
  try {
    const data = await fetchLocationComments(contentid.value)
    comments.value = data.comments
    if (location.value) {
      location.value.comment_count = data.total_count
      location.value.average_rating = data.average_rating
      location.value.rating_count = data.rating_count
    }
  } catch (caught) {
    commentError.value = getApiErrorMessage(caught, '댓글을 불러오지 못했습니다.')
  } finally {
    commentsLoading.value = false
  }
}

async function toggleLike(): Promise<void> {
  if (!location.value || reactionProcessing.value) return
  reactionProcessing.value = true
  actionError.value = ''
  try {
    const result = location.value.liked
      ? await unlikeLocation(location.value.contentid)
      : await likeLocation(location.value.contentid)
    location.value.liked = result.active
    location.value.like_count = result.count
  } catch (caught) {
    actionError.value = getApiErrorMessage(caught, '좋아요 처리에 실패했습니다.')
  } finally {
    reactionProcessing.value = false
  }
}

async function toggleBookmark(): Promise<void> {
  if (!location.value || reactionProcessing.value) return
  reactionProcessing.value = true
  actionError.value = ''
  try {
    const result = location.value.bookmarked
      ? await unbookmarkLocation(location.value.contentid)
      : await bookmarkLocation(location.value.contentid)
    location.value.bookmarked = result.active
    location.value.bookmark_count = result.count
  } catch (caught) {
    actionError.value = getApiErrorMessage(caught, '북마크 처리에 실패했습니다.')
  } finally {
    reactionProcessing.value = false
  }
}

async function submitComment(): Promise<void> {
  commentError.value = ''
  if (!commentForm.content.trim()) {
    commentError.value = '댓글 내용을 입력해 주세요.'
    return
  }
  if (commentForm.password.length < 4) {
    commentError.value = '수정·삭제용 비밀번호를 4자 이상 입력해 주세요.'
    return
  }
  commentSubmitting.value = true
  try {
    await createLocationComment(contentid.value, {
      nickname: commentForm.nickname.trim(),
      content: commentForm.content.trim(),
      rating: commentForm.rating,
      password: commentForm.password,
    })
    commentForm.nickname = ''
    commentForm.content = ''
    commentForm.rating = 0
    commentForm.password = ''
    await loadComments()
  } catch (caught) {
    commentError.value = getApiErrorMessage(caught, '댓글 등록에 실패했습니다.')
  } finally {
    commentSubmitting.value = false
  }
}

function startCommentEdit(comment: LocationComment): void {
  editingCommentId.value = comment.id
  editForm.nickname = comment.nickname === '익명' ? '' : comment.nickname
  editForm.content = comment.content
  editForm.rating = comment.rating
  editForm.password = ''
  commentError.value = ''
}

function cancelCommentEdit(): void {
  editingCommentId.value = null
  editForm.nickname = ''
  editForm.content = ''
  editForm.rating = 0
  editForm.password = ''
}

async function saveCommentEdit(commentId: number): Promise<void> {
  editCommentError.value = ''
  if (!editForm.content.trim()) {
    editCommentError.value = '수정할 댓글 내용을 입력해 주세요.'
    return
  }
  if (editForm.password.length < 4) {
    editCommentError.value = '댓글 작성 시 비밀번호를 입력해 주세요.'
    return
  }
  commentUpdating.value = true
  try {
    await updateLocationComment(contentid.value, commentId, {
      nickname: editForm.nickname.trim(),
      content: editForm.content.trim(),
      rating: editForm.rating,
      password: editForm.password,
    })
    cancelCommentEdit()
    await loadComments()
  } catch (caught) {
    editCommentError.value = getApiErrorMessage(caught, '댓글 수정에 실패했습니다.')
  } finally {
    commentUpdating.value = false
  }
}

function openCommentDelete(commentId: number): void {
  commentDeleteId.value = commentId
  commentDeleteError.value = ''
}

async function confirmCommentDelete(password: string): Promise<void> {
  if (commentDeleteId.value == null) return
  commentDeleting.value = true
  commentDeleteError.value = ''
  try {
    await deleteLocationComment(contentid.value, commentDeleteId.value, password)
    commentDeleteId.value = null
    await loadComments()
  } catch (caught) {
    commentDeleteError.value = getApiErrorMessage(caught, '댓글 삭제에 실패했습니다.')
  } finally {
    commentDeleting.value = false
  }
}

function resetRoutePlanner(): void {
  destinationKeyword.value = ''
  destinationRegion.value = '전체'
  destinationResults.value = []
  destination.value = null
  destinationSearchOpen.value = false
  routeData.value = null
  routeError.value = ''
  routeLoading.value = false
}

async function searchDestinations(): Promise<void> {
  const keyword = destinationKeyword.value.trim()
  if (!keyword) return
  destinationSearching.value = true
  routeError.value = ''
  try {
    const data = await fetchLocations({
      region: destinationRegion.value,
      keyword,
      page: 1,
      size: 10,
    })
    destinationResults.value = data.items.filter((item) => (
      item.contentid !== contentid.value && item.mapx != null && item.mapy != null
    ))
    destinationSearchOpen.value = true
  } catch (caught) {
    routeError.value = getApiErrorMessage(caught, '도착지 검색에 실패했습니다.')
  } finally {
    destinationSearching.value = false
  }
}

function selectDestination(item: Location): void {
  destination.value = item
  destinationKeyword.value = item.title
  destinationResults.value = []
  destinationSearchOpen.value = false
  routeData.value = null
  routeError.value = ''
}

async function findRoute(): Promise<void> {
  if (!location.value || !destination.value || routeLoading.value) {
    routeError.value = '도착할 지역정보를 먼저 선택해 주세요.'
    return
  }
  routeLoading.value = true
  routeError.value = ''
  routeData.value = null
  try {
    routeData.value = await fetchAStarRoute({
      start_contentid: location.value.contentid,
      end_contentid: destination.value.contentid,
      mode: 'drive',
    })
  } catch (caught) {
    routeError.value = getApiErrorMessage(caught, '경로를 계산하지 못했습니다.')
  } finally {
    routeLoading.value = false
  }
}

function clearRoute(): void {
  routeData.value = null
  routeError.value = ''
}

async function autoRouteFromQuery(): Promise<void> {
  // 챗봇에서 '경로 보기'로 진입한 경우 ?to=도착지contentid 를 읽어
  // 도착지를 자동 선택하고 경로 계산까지 바로 수행한다.
  const target = route.query.to
  const endId = Array.isArray(target) ? target[0] : target
  if (!endId || !location.value || endId === location.value.contentid) return
  try {
    const end = await fetchLocation(String(endId))
    if (end.mapx == null || end.mapy == null) {
      routeError.value = '도착지 좌표가 없어 경로를 표시할 수 없습니다.'
      return
    }
    selectDestination(end)
    mapView.value = 'route'
    await findRoute()
  } catch {
    routeError.value = '챗봇이 안내한 도착지를 불러오지 못했습니다.'
  }
}

function formatDistance(meters: number): string {
  return meters >= 1000 ? `${(meters / 1000).toFixed(1)}km` : `${meters}m`
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <div class="page-container detail-page location-detail-page">
    <RouterLink :to="{ path: '/locations', query: { region: route.query.region || location?.region || '전체' } }" class="back-link">
      <ArrowLeft :size="17" /> 지역정보 목록
    </RouterLink>
    <div v-if="loading" class="detail-card skeleton-detail"></div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>

    <template v-else-if="location">
      <article class="detail-card location-main-card">
        <div class="location-detail-hero">
          <img :src="location.firstimage || ''" :alt="location.title" />
        </div>

        <header class="detail-header">
          <div class="post-badges">
            <span class="category-badge">{{ categoryName }}</span>
            <span class="region-badge">{{ location.region }}</span>
          </div>
          <h1>{{ location.title }}</h1>
          <div class="location-detail-info">
            <span><MapPin :size="16" /> {{ location.addr1 || '주소 미제공' }} {{ location.addr2 || '' }}</span>
            <span v-if="location.tel"><Phone :size="16" /> {{ location.tel }}</span>
          </div>
        </header>

        <div class="location-engagement-bar">
          <div class="location-rating-summary">
            <Star :size="22" fill="currentColor" />
            <strong>{{ (location.average_rating || 0).toFixed(1) }}</strong>
            <span>평점 {{ location.rating_count || 0 }}개</span>
          </div>
          <div class="location-stat-list">
            <span><Eye :size="16" /> 조회 {{ location.view_count || 0 }}</span>
            <span><MessageCircle :size="16" /> 댓글 {{ location.comment_count || 0 }}</span>
          </div>
          <div class="location-reaction-actions">
            <div class="reaction-button-group" aria-label="지역정보 반응">
              <button
                type="button"
                :class="['button button-secondary', { selected: location.liked }]"
                :disabled="reactionProcessing"
                @click="toggleLike"
              >
                <Heart :size="17" :fill="location.liked ? 'currentColor' : 'none'" />
                좋아요 {{ location.like_count || 0 }}
              </button>
              <button
                type="button"
                :class="['button button-secondary', { selected: location.bookmarked }]"
                :disabled="reactionProcessing"
                @click="toggleBookmark"
              >
                <Bookmark :size="17" :fill="location.bookmarked ? 'currentColor' : 'none'" />
                북마크 {{ location.bookmark_count || 0 }}
              </button>
            </div>
            <ShareButtons
              kind="location"
              :resource-id="location.contentid"
              :title="location.title"
              :description="shareDescription"
              :image-url="location.firstimage || ''"
              :like-count="location.like_count || 0"
              :comment-count="location.comment_count || 0"
            />
          </div>
        </div>
        <p v-if="actionError" class="form-error location-action-error">{{ actionError }}</p>

        <section v-if="location.mapx != null && location.mapy != null" class="embedded-map-section route-map-section">
          <div class="embedded-map-heading map-section-heading">
            <div><span class="eyebrow">MAP & ROUTE</span><h2>위치 지도와 경로 찾기</h2></div>
            <div class="map-heading-actions">
              <span class="map-coordinate"><MapPin :size="15" /> {{ location.mapy?.toFixed(5) }}, {{ location.mapx?.toFixed(5) }}</span>
              <div class="map-view-toggle" role="tablist" aria-label="지도 화면 선택">
                <button
                  type="button"
                  role="tab"
                  :aria-selected="mapView === 'location'"
                  :class="{ active: mapView === 'location' }"
                  @click="mapView = 'location'"
                >
                  <MapPin :size="15" /> 위치
                </button>
                <button
                  type="button"
                  role="tab"
                  :aria-selected="mapView === 'route'"
                  :class="{ active: mapView === 'route' }"
                  @click="mapView = 'route'"
                >
                  <RouteIcon :size="15" /> 경로찾기
                </button>
              </div>
            </div>
          </div>

          <div v-if="mapView === 'location'" class="location-map-pane">
            <iframe
              v-if="mapEmbedUrl"
              :src="mapEmbedUrl"
              :title="`${location.title} 위치 지도`"
              class="embedded-map"
              loading="lazy"
              referrerpolicy="no-referrer"
            ></iframe>
            <p class="map-attribution">지도 데이터 © OpenStreetMap contributors</p>
          </div>

          <div v-else class="route-map-pane">
            <div class="route-planner-panel">
              <div class="route-start-summary">
                <span class="route-step-badge">출발</span>
                <div>
                  <strong>{{ location.title }}</strong>
                  <small>{{ location.addr1 || '주소 미제공' }}</small>
                </div>
              </div>

              <div class="route-search-grid">
                <label class="route-region-field">
                  <span>검색 지역</span>
                  <select v-model="destinationRegion" class="form-input compact-select">
                    <option value="전체">전체</option>
                    <option value="서울">서울</option>
                    <option value="경기">경기</option>
                  </select>
                </label>

                <div class="route-destination-search">
                  <label for="route-destination">도착할 지역정보</label>
                  <div class="route-search-input-wrap">
                    <Search :size="17" />
                    <input
                      id="route-destination"
                      v-model="destinationKeyword"
                      class="form-input"
                      autocomplete="off"
                      placeholder="장소명 또는 주소 검색"
                      @focus="destinationResults.length && (destinationSearchOpen = true)"
                      @keydown.enter.prevent="searchDestinations"
                    />
                    <LoaderCircle v-if="destinationSearching" :size="17" class="route-spinner" />
                  </div>
                  <ul v-if="destinationSearchOpen" class="route-search-results">
                    <li v-if="destinationResults.length === 0" class="route-search-empty">검색 결과가 없습니다.</li>
                    <li v-for="item in destinationResults" :key="item.contentid">
                      <button type="button" @click="selectDestination(item)">
                        <img :src="item.firstimage || ''" :alt="item.title" />
                        <span>
                          <strong>{{ item.title }}</strong>
                          <small>{{ item.region }} · {{ item.addr1 || '주소 미제공' }}</small>
                        </span>
                      </button>
                    </li>
                  </ul>
                </div>

                <button type="button" class="button button-primary route-find-button" :disabled="routeLoading || !destination" @click="findRoute">
                  <LoaderCircle v-if="routeLoading" :size="17" class="route-spinner" />
                  <Navigation v-else :size="17" />
                  {{ routeLoading ? '탐색 중...' : '경로 찾기' }}
                </button>
              </div>

              <div v-if="location.nearby?.length" class="route-quick-destinations">
                <span>가까운 장소 빠른 선택</span>
                <button
                  v-for="item in location.nearby"
                  :key="item.contentid"
                  type="button"
                  :class="{ active: destination?.contentid === item.contentid }"
                  @click="selectDestination(item)"
                >
                  {{ item.title }}
                </button>
              </div>

              <div v-if="destination" class="route-selected-destination">
                <span class="route-step-badge end">도착</span>
                <div>
                  <strong>{{ destination.title }}</strong>
                  <small>{{ destination.addr1 || '주소 미제공' }}</small>
                </div>
                <button type="button" aria-label="도착지 선택 해제" @click="resetRoutePlanner"><X :size="16" /></button>
              </div>
              <p v-if="routeError" class="form-error route-error">{{ routeError }}</p>
            </div>

            <LocationRouteMap
              :start="location"
              :destination="destination"
              :route-coordinates="routeCoordinates"
            />

            <div v-if="routeData" class="route-summary-grid">
              <div><RouteIcon :size="18" /><span>경로 거리<strong>{{ formatDistance(routeData.distance_m) }}</strong></span></div>
              <div><Car :size="18" /><span>예상 시간(자동차)<strong>약 {{ routeDriveMinutes }}분</strong></span></div>
              <div><Footprints :size="18" /><span>예상 시간(도보)<strong>약 {{ routeWalkMinutes }}분</strong></span></div>
            </div>
            <button v-if="routeData" type="button" class="route-clear-btn" @click="clearRoute">경로 지우기</button>
            <p v-if="routeData" class="route-notice">{{ routeData.notice }}</p>
            <p class="map-attribution">지도·도로 데이터 © OpenStreetMap contributors</p>
          </div>
        </section>
        <div v-else class="map-empty-state"><MapPin :size="24" /> 위치 좌표가 제공되지 않아 지도와 길찾기를 표시할 수 없습니다.</div>
      </article>

      <section v-if="location.nearby?.length" class="content-section nearby-location-section">
        <div class="section-heading">
          <div><span class="eyebrow">NEARBY</span><h2>가까운 지역정보</h2></div>
          <p>현재 장소를 기준으로 가까운 5곳입니다</p>
        </div>
        <div class="location-grid nearby-location-grid">
          <LocationCard v-for="item in location.nearby" :key="item.contentid" :location="item" />
        </div>
      </section>

      <section class="location-review-card">
        <header class="comments-heading">
          <div>
            <span class="eyebrow">REVIEWS</span>
            <h2>별점과 댓글 <strong>{{ comments.length }}</strong></h2>
          </div>
          <div class="review-average"><Star :size="20" fill="currentColor" /> {{ (location.average_rating || 0).toFixed(1) }}</div>
        </header>

        <form class="location-review-form" @submit.prevent="submitComment">
          <div class="review-form-top review-form-three-columns">
            <div class="review-nickname-field">
              <label class="field-label" for="location-nickname">닉네임</label>
              <input
                id="location-nickname"
                v-model="commentForm.nickname"
                class="form-input"
                maxlength="30"
                placeholder="미입력 시 익명"
              />
            </div>
            <div class="review-password-field">
              <label class="field-label" for="location-comment-password">수정·삭제 비밀번호</label>
              <input
                id="location-comment-password"
                v-model="commentForm.password"
                class="form-input"
                type="password"
                minlength="4"
                maxlength="100"
                autocomplete="new-password"
                placeholder="4자 이상"
              />
            </div>
            <div class="review-rating-field">
              <span class="field-label">별점</span>
              <div class="star-picker" aria-label="별점 선택">
                <button
                  v-for="score in 5"
                  :key="score"
                  type="button"
                  :class="{ active: score <= commentForm.rating }"
                  :aria-label="`${score}점`"
                  @click="commentForm.rating = score"
                >
                  <Star :size="25" :fill="score <= commentForm.rating ? 'currentColor' : 'none'" />
                </button>
                <button type="button" class="rating-reset" @click="commentForm.rating = 0">0점</button>
              </div>
            </div>
          </div>
          <label class="field-label" for="location-comment">댓글</label>
          <textarea
            id="location-comment"
            v-model="commentForm.content"
            class="form-input form-textarea"
            maxlength="1000"
            rows="4"
            placeholder="장소에 대한 경험과 정보를 남겨 주세요."
          ></textarea>
          <div class="review-submit-row">
            <p v-if="commentError" class="form-error">{{ commentError }}</p>
            <button type="submit" class="button button-primary" :disabled="commentSubmitting">
              <Send :size="16" /> {{ commentSubmitting ? '등록 중...' : '댓글 등록' }}
            </button>
          </div>
        </form>

        <div v-if="commentsLoading" class="comment-loading">댓글을 불러오는 중입니다.</div>
        <div v-else-if="comments.length === 0" class="comment-empty">첫 번째 별점과 댓글을 남겨 보세요.</div>
        <ol v-else class="location-review-list">
          <li v-for="comment in comments" :key="comment.id" class="location-review-item">
            <template v-if="editingCommentId !== comment.id">
              <div class="location-review-meta">
                <span><UserRound :size="15" /> {{ comment.nickname || '익명' }}</span>
                <div class="review-stars" :aria-label="`${comment.rating}점`">
                  <Star
                    v-for="score in 5"
                    :key="score"
                    :size="15"
                    :class="{ active: score <= comment.rating }"
                    :fill="score <= comment.rating ? 'currentColor' : 'none'"
                  />
                  <small>{{ comment.rating }}점</small>
                </div>
                <time>{{ formatDate(comment.updated_at || comment.created_at) }}<small v-if="comment.updated_at"> 수정됨</small></time>
              </div>
              <p>{{ comment.content }}</p>
              <div class="comment-actions location-comment-actions">
                <button type="button" @click="startCommentEdit(comment)"><Edit3 :size="14" /> 수정</button>
                <button type="button" @click="openCommentDelete(comment.id)"><Trash2 :size="14" /> 삭제</button>
              </div>
            </template>

            <form v-else class="location-comment-edit-form" @submit.prevent="saveCommentEdit(comment.id)">
              <div class="review-form-top review-form-three-columns">
                <div>
                  <label class="field-label" :for="`edit-nickname-${comment.id}`">닉네임</label>
                  <input :id="`edit-nickname-${comment.id}`" v-model="editForm.nickname" class="form-input" maxlength="30" placeholder="미입력 시 익명" />
                </div>
                <div>
                  <label class="field-label" :for="`edit-password-${comment.id}`">작성 시 비밀번호</label>
                  <input :id="`edit-password-${comment.id}`" v-model="editForm.password" class="form-input" type="password" minlength="4" maxlength="100" placeholder="비밀번호" />
                </div>
                <div class="review-rating-field">
                  <span class="field-label">별점</span>
                  <div class="star-picker">
                    <button v-for="score in 5" :key="score" type="button" :class="{ active: score <= editForm.rating }" @click="editForm.rating = score">
                      <Star :size="23" :fill="score <= editForm.rating ? 'currentColor' : 'none'" />
                    </button>
                    <button type="button" class="rating-reset" @click="editForm.rating = 0">0점</button>
                  </div>
                </div>
              </div>
              <textarea v-model="editForm.content" class="form-input form-textarea" maxlength="1000" rows="4"></textarea>
              <p v-if="editCommentError" class="form-error">{{ editCommentError }}</p>
              <div class="comment-edit-actions">
                <button type="button" class="button button-ghost" @click="cancelCommentEdit"><X :size="15" /> 취소</button>
                <button type="submit" class="button button-primary" :disabled="commentUpdating"><Save :size="15" /> {{ commentUpdating ? '저장 중...' : '저장' }}</button>
              </div>
            </form>
          </li>
        </ol>
      </section>

    </template>

    <PasswordModal
      :open="commentDeleteId !== null"
      title="지역정보 댓글 삭제"
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
