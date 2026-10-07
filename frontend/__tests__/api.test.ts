import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from '@/lib/api'

const mockFetch = vi.fn()
global.fetch = mockFetch

beforeEach(() => {
  mockFetch.mockReset()
})

function mockResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  }
}

describe('api.garden', () => {
  it('lists garden items', async () => {
    mockFetch.mockResolvedValue(mockResponse({ results: [], count: 0 }))
    await api.garden.list()
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/garden/'),
      expect.any(Object)
    )
  })

  it('gets a single garden item', async () => {
    mockFetch.mockResolvedValue(mockResponse({ id: 1, name: 'Rose' }))
    const item = await api.garden.get(1)
    expect(item.id).toBe(1)
  })

  it('deletes a garden item', async () => {
    mockFetch.mockResolvedValue({ ok: true, status: 204 })
    await api.garden.delete(1)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/garden/1/'),
      expect.objectContaining({ method: 'DELETE' })
    )
  })
})

describe('api.notifications', () => {
  it('fetches pending notifications', async () => {
    mockFetch.mockResolvedValue(mockResponse([]))
    await api.notifications.pending()
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/notifications/pending/'),
      expect.any(Object)
    )
  })

  it('acknowledges a notification', async () => {
    mockFetch.mockResolvedValue(mockResponse({ id: 1, acknowledged: true }))
    await api.notifications.acknowledge(1)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/notifications/1/acknowledge/'),
      expect.objectContaining({ method: 'POST' })
    )
  })
})

describe('api.llm', () => {
  it('uploads a photo for identification', async () => {
    mockFetch.mockResolvedValue(
      mockResponse({ id: 7, status: 'pending', name: '' }, 201)
    )
    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' })
    const result = await api.llm.identifyUpload(file)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/llm/identify/'),
      expect.objectContaining({ method: 'POST', body: expect.any(FormData) })
    )
    expect(result.id).toBe(7)
    expect(result.status).toBe('pending')
  })

  it('uploads photo as multipart form field named photo', async () => {
    mockFetch.mockResolvedValue(
      mockResponse({ id: 7, status: 'pending', name: '' }, 201)
    )
    const file = new File(['bytes'], 'photo.jpg', { type: 'image/jpeg' })
    await api.llm.identifyUpload(file)
    const form = mockFetch.mock.calls[0][1].body as FormData
    expect(form.get('photo')).toBeInstanceOf(File)
  })

  it('fetches identification status', async () => {
    mockFetch.mockResolvedValue(
      mockResponse({ id: 7, status: 'complete', name: 'Rose' })
    )
    const result = await api.llm.identification(7)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/llm/identify/7/'),
      expect.any(Object)
    )
    expect(result.name).toBe('Rose')
  })

  it('deletes an identification', async () => {
    mockFetch.mockResolvedValue({ ok: true, status: 204 })
    await api.llm.deleteIdentification(7)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/llm/identify/7/'),
      expect.objectContaining({ method: 'DELETE' })
    )
  })
})

describe('api.events', () => {
  it('lists events filtered by week', async () => {
    mockFetch.mockResolvedValue(mockResponse({ results: [], count: 0 }))
    await api.events.list({ week: '2024-W01' })
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('week=2024-W01'),
      expect.any(Object)
    )
  })
})
