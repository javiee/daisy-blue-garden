import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { NotificationItem } from '@/components/NotificationItem'
import type { Notification } from '@/lib/types'

const mockNotification: Notification = {
  id: 1,
  event: 1,
  event_detail: {
    id: 1,
    item: 1,
    item_detail: {
      id: 1,
      name: 'Rose',
      type: 'plant',
      description: '',
      cares: '',
      photo: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    title: 'Water Rose',
    description: 'Water at base',
    date: '2024-03-20',
    recurrence: 'weekly',
    event_type: 'watering',
    created_at: '2024-01-01T00:00:00Z',
  },
  telegram_message_id: '999',
  status: 'sent',
  sent_at: '2024-01-01T00:00:00Z',
  acknowledged: false,
  acknowledged_at: null,
  next_occurrence_date: null,
  created_at: '2024-01-01T00:00:00Z',
}

describe('NotificationItem', () => {
  it('renders notification title', () => {
    render(
      <NotificationItem notification={mockNotification} onAcknowledge={() => {}} isAcknowledging={false} />
    )
    expect(screen.getByText('Water Rose')).toBeDefined()
  })

  it('shows acknowledge button when not acknowledged', () => {
    render(
      <NotificationItem notification={mockNotification} onAcknowledge={() => {}} isAcknowledging={false} />
    )
    expect(screen.getByText('Acknowledge')).toBeDefined()
  })

  it('calls onAcknowledge when button clicked', () => {
    const fn = vi.fn()
    render(
      <NotificationItem notification={mockNotification} onAcknowledge={fn} isAcknowledging={false} />
    )
    fireEvent.click(screen.getByText('Acknowledge'))
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('does not show acknowledge button when already acknowledged', () => {
    render(
      <NotificationItem
        notification={{ ...mockNotification, acknowledged: true }}
        onAcknowledge={() => {}}
        isAcknowledging={false}
      />
    )
    expect(screen.queryByText('Acknowledge')).toBeNull()
  })
})
