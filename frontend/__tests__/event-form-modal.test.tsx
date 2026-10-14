import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { CalendarEvent, GardenItem } from '@/lib/types'

const mockCreateMutate = vi.fn()
const mockUpdateMutate = vi.fn()
vi.mock('@/lib/hooks', () => ({
  useCreateEvent: () => ({ mutateAsync: mockCreateMutate, isPending: false }),
  useUpdateEvent: () => ({ mutateAsync: mockUpdateMutate, isPending: false }),
}))

import { EventFormModal } from '@/components/EventFormModal'

const item: GardenItem = {
  id: 1,
  name: 'Rose',
  type: 'plant',
  description: '',
  cares: '',
  photo: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const baseEvent: CalendarEvent = {
  id: 9,
  item: 1,
  item_detail: item,
  title: 'Fertilize monthly',
  description: 'Use compost',
  date: '2026-02-15',
  recurrence: 'monthly',
  event_type: 'fertilizing',
  is_manual: true,
  created_at: '2026-01-01T00:00:00Z',
  parent_event: null,
  end_date: '2026-06-30',
  repeats_yearly: true,
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('EventFormModal (create mode)', () => {
  it('shows the repeat-every-year checkbox checked by default', () => {
    render(<EventFormModal itemId={1} onClose={vi.fn()} />)
    const checkbox = screen.getByRole('checkbox', { name: /repeat every year/i })
    expect(checkbox).toBeChecked()
  })

  it('submits a new event with repeats_yearly true when the checkbox is left on', async () => {
    const user = userEvent.setup()
    render(<EventFormModal itemId={1} onClose={vi.fn()} />)
    await user.type(screen.getByPlaceholderText(/water deeply/i), 'Water deeply')
    await user.click(screen.getByRole('button', { name: /add event/i }))
    expect(mockCreateMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Water deeply',
        repeats_yearly: true,
        is_manual: true,
      })
    )
  })
})

describe('EventFormModal (general task, no item)', () => {
  const taskEvent: CalendarEvent = {
    ...baseEvent,
    id: 42,
    item: null,
    item_detail: null,
    title: 'Mow lawn',
    description: '',
    date: '2026-10-20',
    recurrence: 'weekly',
    event_type: 'other',
    end_date: null,
    repeats_yearly: false,
  }

  it('creates a task event without an item when no itemId is given', async () => {
    const user = userEvent.setup()
    render(<EventFormModal onClose={vi.fn()} />)
    await user.type(screen.getByPlaceholderText(/water deeply/i), 'Mow lawn')
    await user.click(screen.getByRole('button', { name: /add event/i }))
    expect(mockCreateMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Mow lawn',
        item: null,
        is_manual: true,
      })
    )
  })

  it('keeps item null when editing a task event', async () => {
    const user = userEvent.setup()
    render(<EventFormModal event={taskEvent} onClose={vi.fn()} />)
    await user.click(screen.getByRole('button', { name: /^save$/i }))
    expect(mockUpdateMutate).toHaveBeenCalledWith({
      id: 42,
      data: expect.objectContaining({
        item: null,
        title: 'Mow lawn',
      }),
    })
  })
})

describe('EventFormModal (edit mode)', () => {
  it('prefills fields from the event and shows a checked repeat checkbox', () => {
    render(<EventFormModal itemId={1} event={baseEvent} onClose={vi.fn()} />)
    expect(screen.getByDisplayValue('Fertilize monthly')).toBeInTheDocument()
    expect(screen.getByDisplayValue('2026-02-15')).toBeInTheDocument()
    expect(screen.getByDisplayValue('2026-06-30')).toBeInTheDocument()
    expect(
      screen.getByRole('checkbox', { name: /repeat every year/i })
    ).toBeChecked()
    expect(screen.getByRole('heading', { name: /edit care event/i })).toBeInTheDocument()
  })

  it('saves changes via the update mutation, including an unticked repeat checkbox', async () => {
    const user = userEvent.setup()
    render(<EventFormModal itemId={1} event={baseEvent} onClose={vi.fn()} />)
    await user.click(screen.getByRole('checkbox', { name: /repeat every year/i }))
    await user.click(screen.getByRole('button', { name: /^save$/i }))
    expect(mockUpdateMutate).toHaveBeenCalledWith({
      id: baseEvent.id,
      data: expect.objectContaining({
        title: 'Fertilize monthly',
        date: '2026-02-15',
        recurrence: 'monthly',
        end_date: '2026-06-30',
        repeats_yearly: false,
      }),
    })
  })

  it('hides the repeat checkbox for yearly events (they repeat by definition)', () => {
    render(
      <EventFormModal
        itemId={1}
        event={{ ...baseEvent, recurrence: 'yearly', repeats_yearly: true }}
        onClose={vi.fn()}
      />
    )
    expect(screen.queryByRole('checkbox')).toBeNull()
  })
})
