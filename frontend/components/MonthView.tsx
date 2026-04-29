import { startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, isSameMonth, isSameDay, format, parseISO } from 'date-fns'
import type { CalendarEvent } from '@/lib/types'

const EVENT_COLORS: Record<string, string> = {
  watering: 'bg-blue-400',
  fertilizing: 'bg-green-400',
  pruning: 'bg-orange-400',
  other: 'bg-gray-400',
}

interface Props {
  events: CalendarEvent[]
  currentDate: Date
}

export function MonthView({ events, currentDate }: Props) {
  const monthStart = startOfMonth(currentDate)
  const monthEnd = endOfMonth(currentDate)
  const gridStart = startOfWeek(monthStart, { weekStartsOn: 1 })
  const gridEnd = endOfWeek(monthEnd, { weekStartsOn: 1 })
  const days = eachDayOfInterval({ start: gridStart, end: gridEnd })

  return (
    <div className="overflow-x-auto">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow overflow-hidden min-w-[320px]">
        {/* Day headers */}
        <div className="grid grid-cols-7 border-b border-gray-100 dark:border-slate-700">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => (
            <div key={d} className="text-center py-3 text-xs font-semibold text-gray-500 dark:text-gray-400">
              {d}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7">
          {days.map((day) => {
            const dayEvents = events.filter((e) => isSameDay(parseISO(e.date), day))
            const isCurrentMonth = isSameMonth(day, currentDate)
            const isToday = isSameDay(day, new Date())

            return (
              <div
                key={day.toISOString()}
                className={`min-h-24 p-2 border-b border-r border-gray-100 dark:border-slate-700 ${!isCurrentMonth ? 'opacity-30' : ''}`}
              >
                <div className={`w-7 h-7 flex items-center justify-center rounded-full text-sm font-medium mb-1 ${isToday ? 'bg-green-600 text-white' : 'text-gray-700 dark:text-gray-300'}`}>
                  {format(day, 'd')}
                </div>
                <div className="space-y-0.5">
                  {dayEvents.slice(0, 3).map((event) => (
                    <div
                      key={event.id}
                      className={`h-2 rounded-full ${EVENT_COLORS[event.event_type] ?? 'bg-gray-400'}`}
                      title={event.title}
                    />
                  ))}
                  {dayEvents.length > 3 && (
                    <div className="text-xs text-gray-400">+{dayEvents.length - 3}</div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 px-4 py-3 border-t border-gray-100 dark:border-slate-700">
          {Object.entries(EVENT_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5">
              <div className={`w-3 h-3 rounded-full ${color}`} />
              <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
