export type GardenItemType = 'plant' | 'tree' | 'shrub' | 'other'
export type EventType = 'watering' | 'fertilizing' | 'pruning' | 'other'
export type RecurrenceType = 'once' | 'weekly' | 'monthly' | 'yearly'
export type NotificationStatus = 'pending' | 'sent' | 'failed'
export type NotificationFrequency = 'daily' | 'weekly' | 'monthly'

export interface GardenItem {
  id: number
  name: string
  type: GardenItemType
  description: string
  cares: string
  photo: string | null
  created_at: string
  updated_at: string
}

export interface CalendarEvent {
  id: number
  item: number
  item_detail: GardenItem
  title: string
  description: string
  date: string
  recurrence: RecurrenceType
  event_type: EventType
  created_at: string
}

export interface Notification {
  id: number
  event: number
  event_detail: CalendarEvent
  telegram_message_id: string
  status: NotificationStatus
  sent_at: string | null
  acknowledged: boolean
  acknowledged_at: string | null
  next_occurrence_date: string | null
  created_at: string
}

export interface NotificationConfig {
  id: number
  telegram_chat_id: string
  frequency: NotificationFrequency
  days_before: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
