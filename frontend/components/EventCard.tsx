'use client'

import { useState } from 'react'
import { Trash2, X, Check } from 'lucide-react'
import type { CalendarEvent } from '@/lib/types'
import { EventTypeIcon } from './EventTypeIcon'
import { formatDate } from '@/lib/utils'

interface EventCardProps {
  event: CalendarEvent
  onDelete?: (id: number) => Promise<unknown>
}

export function EventCard({ event, onDelete }: EventCardProps) {
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function handleDelete() {
    if (!onDelete) return
    setDeleting(true)
    await onDelete(event.id)
    setDeleting(false)
  }

  return (
    <div className="group flex items-start gap-3 p-3 rounded-xl bg-gray-50 dark:bg-slate-700 hover:bg-gray-100 dark:hover:bg-slate-600 transition-colors">
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
          {event.is_manual && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 font-medium">
              Manual
            </span>
          )}
        </div>
      </div>

      {onDelete && (
        <div className="flex-shrink-0 flex items-center gap-1">
          {confirming ? (
            <>
              <button
                onClick={handleDelete}
                disabled={deleting}
                title="Confirm delete"
                className="p-1.5 rounded-lg bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900 transition-colors disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setConfirming(false)}
                title="Cancel"
                className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-400 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </>
          ) : (
            <button
              onClick={() => setConfirming(true)}
              title="Delete event"
              className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-50 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-500 transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
