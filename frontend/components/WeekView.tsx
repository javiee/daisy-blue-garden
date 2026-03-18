import { startOfWeek, addDays, format, isSameDay } from 'date-fns'
import type { CalendarEvent } from '@/lib/types'
import { EventTypeIcon } from './EventTypeIcon'

interface Props {
  events: CalendarEvent[]
  currentDate: Date
}

export function WeekView({ events, currentDate }: Props) {
  const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 })
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))

  return (
    <div className="grid grid-cols-7 gap-2">
      {days.map((day) => {
        const dayEvents = events.filter((e) => isSameDay(new Date(e.date), day))
        const isToday = isSameDay(day, new Date())
        return (
          <div key={day.toISOString()} className="min-h-32">
            <div className={`text-center py-2 rounded-t-lg text-sm font-medium ${isToday ? 'bg-green-600 text-white' : 'bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400'}`}>
              <div>{format(day, 'EEE')}</div>
              <div className="text-lg font-bold">{format(day, 'd')}</div>
            </div>
            <div className="space-y-1 p-1 bg-white dark:bg-slate-800 rounded-b-lg min-h-24 border border-gray-100 dark:border-slate-700">
              {dayEvents.map((event) => (
                <div
                  key={event.id}
                  className="text-xs p-1.5 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 hover:bg-green-100 transition-colors cursor-pointer"
                  title={event.description}
                >
                  <div className="font-medium text-green-800 dark:text-green-200 line-clamp-1">
                    {event.title}
                  </div>
                  <EventTypeIcon type={event.event_type} />
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
