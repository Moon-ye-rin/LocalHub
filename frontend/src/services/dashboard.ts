import api from './api'
import type { ApiResponse, DashboardData } from '@/types'

export async function fetchDashboard(): Promise<DashboardData> {
  const { data } = await api.get<ApiResponse<DashboardData>>('/api/dashboard')
  return data.data
}
