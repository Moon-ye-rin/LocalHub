export interface ApiResponse<T> {
  success: boolean
  data: T
  message: string | null
}

export interface Post {
  id: number
  category: string
  region: '서울' | '경기' | null
  district: string | null
  title: string
  content: string
  view_count: number
  like_count: number
  comment_count: number
  tags: string[]
  images?: string[]
  liked?: boolean
  created_at: string
  updated_at: string | null
}

export interface PostPayload {
  category: string
  region: '서울' | '경기'
  district: string
  title: string
  content: string
  password: string
  tags: string[]
}

export interface PostListData {
  posts: Post[]
  page: number
  size: number
  total_count: number
  total_pages: number
}

export interface Comment {
  id: number
  post_id: number
  content: string
  created_at: string
  updated_at: string | null
}

export interface CommentListData {
  comments: Comment[]
  total_count: number
}

export interface CommentPayload {
  content: string
  password: string
}

export interface Location {
  contentid: string
  contenttypeid: string
  region: string
  title: string
  addr1: string | null
  addr2: string | null
  tel: string | null
  mapx: number | null
  mapy: number | null
  lDongRegnCd: string | null
  lDongSignguCd: string | null
  lclsSystm1: string | null
  lclsSystm2: string | null
  lclsSystm3: string | null
  firstimage: string | null
  firstimage2: string | null
  cpyrhtDivCd: string | null
  bookmarked?: boolean
  zipcode?: string | null
  mlevel?: string | null
  createdtime?: string | null
  modifiedtime?: string | null
  view_count?: number
  like_count?: number
  bookmark_count?: number
  comment_count?: number
  average_rating?: number
  rating_count?: number
  liked?: boolean
  nearby?: Location[]
}

export interface LocationComment {
  id: number
  contentid: string
  nickname: string
  content: string
  rating: number
  created_at: string
  updated_at: string | null
}

export interface LocationCommentPayload {
  nickname: string
  content: string
  rating: number
  password: string
}

export interface LocationCommentListData {
  comments: LocationComment[]
  total_count: number
  average_rating: number
  rating_count: number
}

export interface LocationListData {
  region: string
  items: Location[]
  page: number
  size: number
  total_count: number
  total_pages: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatReference {
  type: 'location' | 'post'
  id: string
  name: string
}

export interface ChatData {
  reply: string
  references: ChatReference[]
  mode: 'local' | 'openai'
  source_notice: string
}

export const CATEGORY_OPTIONS = [
  { code: '12', label: '관광지' },
  { code: '14', label: '문화시설' },
  { code: '15', label: '축제공연행사' },
  { code: '25', label: '여행코스' },
  { code: '28', label: '레포츠' },
  { code: '32', label: '숙박' },
  { code: '38', label: '쇼핑' },
  { code: '39', label: '음식점' },
]


export type RouteMode = 'walk' | 'drive'

export interface AStarRouteRequest {
  start_contentid: string
  end_contentid: string
  mode: RouteMode
}

export interface AStarRoutePoint {
  contentid: string
  title: string
  latitude: number
  longitude: number
}

export interface AStarRouteData {
  algorithm: 'A*'
  mode: RouteMode
  start: AStarRoutePoint
  end: AStarRoutePoint
  distance_m: number
  direct_distance_m: number
  estimated_minutes: number
  drive_minutes?: number
  walk_minutes?: number
  explored_nodes: number
  coordinates: [number, number][]
  attribution: string
  notice: string
}


export interface DashboardSeries {
  name: string
  data: number[]
}

export interface CategorySlice {
  label: string
  count: number
}

export interface PopularRegion {
  region: '서울' | '경기'
  district: string
  label: string
  score: number
  post_count: number
  comment_count: number
  like_count: number
  view_count: number
}

export interface PopularLocation {
  contentid: string
  title: string
  region: string
  firstimage: string | null
  score: number
  comment_count: number
  like_count: number
  view_count: number
  average_rating: number
  rating_count: number
}

export interface TopRatedLocation {
  contentid: string
  title: string
  region: string
  firstimage: string | null
  average_rating: number
  rating_count: number
  comment_count: number
}

export interface DashboardData {
  monthly_category: {
    labels: string[]
    series: DashboardSeries[]
  }
  category_distribution: {
    total: CategorySlice[]
    seoul: CategorySlice[]
    gyeonggi: CategorySlice[]
  }
  popular_regions: PopularRegion[]
  popular_locations: PopularLocation[]
  top_rated_locations: TopRatedLocation[]
  weekly_trend: {
    labels: string[]
    views: number[]
    likes: number[]
  }
  score_formula: string
}
