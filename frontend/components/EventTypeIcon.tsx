import type { EventType } from '@/lib/types'

const ICONS: Record<EventType, string> = {
  watering: '💧',
  fertilizing: '🌱',
  pruning: '✂️',
  other: '📋',
}

const COLORS: Record<EventType, string> = {
  watering: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  fertilizing: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  pruning: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
  other: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
}

export function EventTypeIcon({ type }: { type: EventType }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${COLORS[type] ?? COLORS.other}`}>
      {ICONS[type] ?? '📋'} {type}
    </span>
  )
}
