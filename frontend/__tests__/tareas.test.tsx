import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { CalendarEvent } from '@/lib/types'

const mockDelete = vi.fn()
const mockCreate = vi.fn()
const mockUpdate = vi.fn()
let mockResults: CalendarEvent[] = []

vi.mock('@/lib/hooks', () => ({
  useGeneralEvents: () => ({
    data: { results: mockResults, count: mockResults.length },
    isLoading: false,
  }),
  useDeleteEvent: () => ({ mutateAsync: mockDelete }),
  useCreateEvent: () => ({ mutateAsync: mockCreate, isPending: false }),
  useUpdateEvent: () => ({ mutateAsync: mockUpdate, isPending: false }),
}))

import { default as TasksPage } from '@/app/tareas/page'

const task: CalendarEvent = {
  id: 5,
  item: null,
  item_detail: null,
  title: 'Mow lawn',
  description: 'After rain',
  date: '2026-10-20',
  recurrence: 'weekly',
  event_type: 'other',
  is_manual: true,
  created_at: '2026-01-01T00:00:00Z',
  parent_event: null,
  end_date: null,
  repeats_yearly: false,
}

beforeEach(() => {
  vi.clearAllMocks()
  mockResults = [task]
})

describe('Tasks page (Tareas)', () => {
  it('shows the section title and the saved tasks', () => {
    render(<TasksPage />)
    expect(screen.getByRole('heading', { name: /garden care/i })).toBeInTheDocument()
    expect(screen.getByText('Mow lawn')).toBeInTheDocument()
  })

  it('shows an empty state when there are no tasks', () => {
    mockResults = []
    render(<TasksPage />)
    expect(screen.getByText(/no garden tasks/i)).toBeInTheDocument()
  })

  it('opens the event form from the add button', async () => {
    const user = userEvent.setup()
    render(<TasksPage />)
    await user.click(screen.getByRole('button', { name: /add task/i }))
    expect(
      screen.getByRole('heading', { name: /add care event/i })
    ).toBeInTheDocument()
  })

  it('deletes a task through the confirm flow', async () => {
    const user = userEvent.setup()
    render(<TasksPage />)
    await user.click(screen.getByRole('button', { name: /delete event/i }))
    await user.click(screen.getByRole('button', { name: /confirm delete/i }))
    expect(mockDelete).toHaveBeenCalledWith(5)
  })
})
