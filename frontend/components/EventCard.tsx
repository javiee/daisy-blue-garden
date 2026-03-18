import type { CalendarEvent } from '@/lib/types'
import { EventTypeIcon } from './EventTypeIcon'
import { formatDate } from '@/lib/utils'

export function EventCard({ event }: { event: CalendarEvent }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-xl bg-gray-50 dark:bg-slate-700 hover:bg-gray-100 dark:hover:bg-slate-600 transition-colors">
      <div className="flex-shrink-0 mt-0.5">
        <EventTypeIcon type={event.event_type} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="font-medium text-gray-800 dark:text-gray-100 text-sm">{event.title}</p>
        {event.description && (
          <p className="text-gray-500 dark:text-gray-400 text-xs mt-0.5 line-clamp-2">
            {event.description}
          </p>
        )}
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-400">{formatDate(event.date)}</span>
          <span className="text-xs text-gray-300">·</span>
          <span className="text-xs text-gray-400 capitalize">{event.recurrence}</span>
        </div>
      </div>
    </div>
  )
}
