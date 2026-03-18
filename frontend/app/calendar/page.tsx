'use client'

import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { format, addWeeks, subWeeks, addMonths, subMonths } from 'date-fns'
import { useCalendarEvents } from '@/lib/hooks'
import { WeekView } from '@/components/WeekView'
import { MonthView } from '@/components/MonthView'
import { getWeekString, getMonthString } from '@/lib/utils'

type ViewMode = 'week' | 'month'

export default function CalendarPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('week')
  const [currentDate, setCurrentDate] = useState(new Date())

  const params =
    viewMode === 'week'
      ? { week: getWeekString(currentDate) }
      : { month: getMonthString(currentDate) }

  const { data, isLoading } = useCalendarEvents(params)
  const events = data?.results ?? []

  const navigate = (direction: 'prev' | 'next') => {
    if (viewMode === 'week') {
      setCurrentDate(direction === 'prev' ? subWeeks(currentDate, 1) : addWeeks(currentDate, 1))
    } else {
      setCurrentDate(direction === 'prev' ? subMonths(currentDate, 1) : addMonths(currentDate, 1))
    }
  }

  const title =
    viewMode === 'week'
      ? `Week of ${format(currentDate, 'MMM d, yyyy')}`
      : format(currentDate, 'MMMM yyyy')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-green-800 dark:text-green-200">Calendar</h1>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg overflow-hidden border border-green-200 dark:border-green-700">
            <button
              onClick={() => setViewMode('week')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                viewMode === 'week'
                  ? 'bg-green-600 text-white'
                  : 'bg-white dark:bg-slate-800 text-green-700 dark:text-green-300 hover:bg-green-50'
              }`}
            >
              Week
            </button>
            <button
              onClick={() => setViewMode('month')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                viewMode === 'month'
                  ? 'bg-green-600 text-white'
                  : 'bg-white dark:bg-slate-800 text-green-700 dark:text-green-300 hover:bg-green-50'
              }`}
            >
              Month
            </button>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between bg-white dark:bg-slate-800 rounded-xl p-4 shadow">
        <button
          onClick={() => navigate('prev')}
          className="p-2 rounded-lg hover:bg-green-50 dark:hover:bg-slate-700 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-green-700 dark:text-green-300" />
        </button>
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">{title}</h2>
        <button
          onClick={() => navigate('next')}
          className="p-2 rounded-lg hover:bg-green-50 dark:hover:bg-slate-700 transition-colors"
        >
          <ChevronRight className="w-5 h-5 text-green-700 dark:text-green-300" />
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : viewMode === 'week' ? (
        <WeekView events={events} currentDate={currentDate} />
      ) : (
        <MonthView events={events} currentDate={currentDate} />
      )}
    </div>
  )
}
