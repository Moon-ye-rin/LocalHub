import api from './api'
import type {
  ApiResponse,
  Location,
  LocationCommentListData,
  LocationCommentPayload,
  LocationListData,
} from '@/types'

export interface LocationQuery {
  region?: '서울' | '경기'
  bookmarked_only?: boolean
  contenttypeid?: string
  keyword?: string
  lDongSignguCd?: string
  lclsSystm1?: string
  lclsSystm2?: string
  lclsSystm3?: string
  page?: number
  size?: number
}

export async function fetchLocations(params: LocationQuery = {}): Promise<LocationListData> {
  const { data } = await api.get<ApiResponse<LocationListData>>('/api/locations', { params })
  return data.data
}

export async function fetchLocation(contentid: string): Promise<Location> {
  const { data } = await api.get<ApiResponse<Location>>(`/api/locations/${contentid}`)
  return data.data
}

export async function fetchLocationComments(contentid: string): Promise<LocationCommentListData> {
  const { data } = await api.get<ApiResponse<LocationCommentListData>>(`/api/locations/${contentid}/comments`)
  return data.data
}

export async function createLocationComment(contentid: string, payload: LocationCommentPayload): Promise<number> {
  const { data } = await api.post<ApiResponse<{ id: number }>>(`/api/locations/${contentid}/comments`, payload)
  return data.data.id
}

export async function updateLocationComment(
  contentid: string,
  commentId: number,
  payload: LocationCommentPayload,
): Promise<number> {
  const { data } = await api.put<ApiResponse<{ id: number }>>(
    `/api/locations/${contentid}/comments/${commentId}`,
    payload,
  )
  return data.data.id
}

export async function deleteLocationComment(
  contentid: string,
  commentId: number,
  password: string,
): Promise<void> {
  await api.delete(`/api/locations/${contentid}/comments/${commentId}`, {
    data: { password },
  })
}

export async function likeLocation(contentid: string): Promise<{ count: number; active: boolean }> {
  const { data } = await api.post<ApiResponse<{ count: number; active: boolean }>>(`/api/locations/${contentid}/like`)
  return data.data
}

export async function unlikeLocation(contentid: string): Promise<{ count: number; active: boolean }> {
  const { data } = await api.delete<ApiResponse<{ count: number; active: boolean }>>(`/api/locations/${contentid}/like`)
  return data.data
}

export async function bookmarkLocation(contentid: string): Promise<{ count: number; active: boolean }> {
  const { data } = await api.post<ApiResponse<{ count: number; active: boolean }>>(`/api/locations/${contentid}/bookmark`)
  return data.data
}

export async function unbookmarkLocation(contentid: string): Promise<{ count: number; active: boolean }> {
  const { data } = await api.delete<ApiResponse<{ count: number; active: boolean }>>(`/api/locations/${contentid}/bookmark`)
  return data.data
}
