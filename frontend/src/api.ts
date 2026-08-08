import axios from 'axios'
import type { AuthResponse, User } from './types'

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1' })
api.interceptors.request.use((config) => { const token = localStorage.getItem('access_token'); if (token) config.headers.Authorization = `Bearer ${token}`; return config })
export const authApi = {
  register: (full_name: string, email: string, password: string) => api.post<AuthResponse>('/auth/register', { full_name, email, password }),
  login: (email: string, password: string) => api.post<AuthResponse>('/auth/login', { email, password }),
  logout: (refresh_token: string) => api.post('/auth/logout', { refresh_token }),
  me: () => api.get<User>('/auth/me'),
  forgot: (email: string) => api.post('/auth/forgot-password', { email }),
  reset: (token: string, password: string) => api.post('/auth/reset-password', { token, password }),
}
export type DashboardSummary = {
  user_name: string; stats: { total_predictions: number; unread_notifications: number; latest_crop: Record<string, unknown> | null; soil_health: Record<string, unknown> | null; disease_status: string | null }
  weather: Record<string, unknown> | null; notifications: { id: number; category: string; title: string; message: string; is_read: boolean; created_at: string }[]
  recent_predictions: { id: number; type: string; result: Record<string, unknown>; confidence: number | null; created_at: string }[]; timeline: { date: string; count: number }[]
}
export const dashboardApi = { summary: () => api.get<DashboardSummary>('/dashboard/summary') }
export const agricultureApi = {
  crop: (data: unknown) => api.post('/crop-predictions', data), fertilizer: (data: unknown) => api.post('/fertilizer-recommendations', data), yield: (data: unknown) => api.post('/yield-predictions', data), soil: (data: unknown) => api.post('/soil-health', data), irrigation: (data: unknown) => api.post('/irrigation-recommendations', data), market: (data: unknown) => api.post('/market-price-predictions', data), weather: (data: unknown) => api.post('/weather', data), chat: (message: string) => api.post('/chat', { message }), history: () => api.get('/chat/history'), report: (type: string) => api.post(`/reports/${type}`), adminUsers: () => api.get('/admin/users'), adminAnalytics: () => api.get('/admin/analytics'),
  disease: (file: File, crop: string) => { const body = new FormData(); body.append('image', file); if (crop) body.append('crop', crop); return api.post('/disease-detections', body) },
  dataset: (name: string, domain: string, file: File) => { const body = new FormData(); body.append('name', name); body.append('domain', domain); body.append('file', file); return api.post('/admin/datasets', body) },
  train: (id: number, target: string) => api.post(`/admin/datasets/${id}/train?target_column=${encodeURIComponent(target)}`),
}
