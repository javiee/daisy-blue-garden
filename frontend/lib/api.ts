import type {
  AppSettings,
  GardenItem,
  CalendarEvent,
  Notification,
  NotificationConfig,
  PaginatedResponse,
  PlantIdentification,
} from './types'

// No fixed host: the API runs on this same machine (port 8000), so call it
// via whatever hostname the app was loaded from (works on LAN phones too,
// and survives the Mac's DHCP IP changing). NEXT_PUBLIC_API_URL overrides.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== 'undefined'
    ? `http://${window.location.hostname}:8000/api/v1`
    : 'http://localhost:8000/api/v1')

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
    patch: (id: number, data: Partial<GardenItem>) =>
      request<GardenItem>(`/garden/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    patchPhoto: (id: number, photo: File) => {
      const form = new FormData()
      form.append('photo', photo)
      return fetch(`${API_BASE}/garden/${id}/`, { method: 'PATCH', body: form }).then((r) => {
        if (!r.ok) throw new Error('Failed to upload photo')
        return r.json() as Promise<GardenItem>
      })
    },
    delete: (id: number) => request<void>(`/garden/${id}/`, { method: 'DELETE' }),
  },

  events: {
    list: (params?: { week?: string; month?: string; item?: number; base_only?: string }) => {
      const qs = params ? '?' + new URLSearchParams(params as Record<string, string>).toString() : ''
      return request<PaginatedResponse<CalendarEvent>>(`/events/${qs}`)
    },
    byItem: (itemId: number, params?: Record<string, string>) => {
      const qs = params ? '?' + new URLSearchParams(params).toString() : ''
      return request<CalendarEvent[]>(`/events/by-item/${itemId}/${qs}`)
    },
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
    testNotification: (id: number) =>
      request<{ status: string; message_id?: string }>(`/notifications/config/${id}/test/`, {
      method: 'POST',
    }),
  },

  llm: {
    generateCare: (itemId: number) =>
      request<{ task_id: string; status: string }>(`/llm/generate-care/${itemId}/`, {
        method: 'POST',
      }),
    identifyUpload: (photo: File) => {
      const form = new FormData()
      form.append('photo', photo)
      return fetch(`${API_BASE}/llm/identify/`, { method: 'POST', body: form }).then((r) => {
        if (!r.ok) throw new Error('Failed to upload photo for identification')
        return r.json() as Promise<PlantIdentification>
      })
    },
    identification: (id: number) => request<PlantIdentification>(`/llm/identify/${id}/`),
    deleteIdentification: (id: number) =>
      request<void>(`/llm/identify/${id}/`, { method: 'DELETE' }),
  },

  settings: {
    get: () => request<AppSettings>('/settings/'),
    save: (data: Partial<AppSettings>) =>
      request<AppSettings>('/settings/', {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
  },
}
