'use client'

import { useState } from 'react'
import { Plus, ListChecks } from 'lucide-react'
import { useGeneralEvents, useDeleteEvent } from '@/lib/hooks'
import { EventCard } from '@/components/EventCard'
import { EventFormModal } from '@/components/EventFormModal'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'
import { useI18n } from '@/lib/i18n'
import type { CalendarEvent } from '@/lib/types'

export default function TasksPage() {
  const { t } = useI18n()
  const { data, isLoading } = useGeneralEvents()
  const deleteEvent = useDeleteEvent()
  const [showAdd, setShowAdd] = useState(false)
  const [editing, setEditing] = useState<CalendarEvent | null>(null)
  const tasks = data?.results ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ListChecks className="w-7 h-7 text-green-600 dark:text-green-300" />
          <div>
            <h1 className="text-3xl font-bold text-green-800 dark:text-green-200">
              {t('tasks.title')}
            </h1>
            <p className="text-sm text-green-600 dark:text-green-400">
              {t('tasks.subtitle')}
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium shadow transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t('tasks.addTask')}
        </button>
      </div>

      {/* Task list */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : tasks.length > 0 ? (
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-6 space-y-3">
          {tasks.map((task) => (
            <EventCard
              key={task.id}
              event={task}
              onDelete={(id) => deleteEvent.mutateAsync(id)}
              onEdit={(event) => setEditing(event)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-white dark:bg-slate-800 rounded-2xl shadow">
          <div className="text-6xl mb-4">🌿</div>
          <p className="text-gray-500 dark:text-gray-400">{t('tasks.noTasks')}</p>
        </div>
      )}

      {showAdd && <EventFormModal onClose={() => setShowAdd(false)} />}

      {editing && (
        <EventFormModal event={editing} onClose={() => setEditing(null)} />
      )}
    </div>
  )
}
