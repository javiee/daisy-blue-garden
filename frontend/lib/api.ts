import type {
  GardenItem,
  CalendarEvent,
  Notification,
  NotificationConfig,
  PaginatedResponse,
} from './types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || `Request failed: ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  garden: {
    list: (params?: Record<string, string>) => {
      const qs = params ? '?' + new URLSearchParams(params).toString() : ''
      return request<PaginatedResponse<GardenItem>>(`/garden/${qs}`)
    },
    get: (id: number) => request<GardenItem>(`/garden/${id}/`),
    create: (data: FormData) =>
      fetch(`${API_BASE}/garden/`, { method: 'POST', body: data }).then((r) => {
        if (!r.ok) throw new Error('Failed to create item')
        return r.json() as Promise<GardenItem>
      }),
    update: (id: number, data: Partial<GardenItem>) =>
      request<GardenItem>(`/garden/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: number) => request<void>(`/garden/${id}/`, { method: 'DELETE' }),
  },

  events: {
    list: (params?: { week?: string; month?: string; item?: number }) => {
      const qs = params ? '?' + new URLSearchParams(params as Record<string, string>).toString() : ''
      return request<PaginatedResponse<CalendarEvent>>(`/events/${qs}`)
    },
    byItem: (itemId: number) =>
      request<CalendarEvent[]>(`/events/by-item/${itemId}/`),
    create: (data: Partial<CalendarEvent>) =>
      request<CalendarEvent>('/events/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<CalendarEvent>) =>
      request<CalendarEvent>(`/events/${id}/`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request<void>(`/events/${id}/`, { method: 'DELETE' }),
  },

  notifications: {
    list: () => request<PaginatedResponse<Notification>>('/notifications/'),
    pending: () => request<Notification[]>('/notifications/pending/'),
    acknowledge: (id: number) =>
      request<Notification>(`/notifications/${id}/acknowledge/`, { method: 'POST' }),
    getConfig: () => request<PaginatedResponse<NotificationConfig>>('/notifications/config/'),
    saveConfig: (data: Partial<NotificationConfig>) =>
      request<NotificationConfig>('/notifications/config/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  llm: {
    generateCare: (itemId: number) =>
      request<{ task_id: string; status: string }>(`/llm/generate-care/${itemId}/`, {
        method: 'POST',
      }),
  },
}
