import api from './api'
import type { ApiResponse, AStarRouteData, AStarRouteRequest } from '@/types'

export async function fetchAStarRoute(payload: AStarRouteRequest): Promise<AStarRouteData> {
  const { data } = await api.post<ApiResponse<AStarRouteData>>('/api/routes/astar', payload)
  return data.data
}
