'use client'

import { useState } from 'react'
import { X } from 'lucide-react'
import type { CalendarEvent, EventType, RecurrenceType } from '@/lib/types'
import { useCreateEvent, useUpdateEvent } from '@/lib/hooks'
import { useI18n } from '@/lib/i18n'
import type { TKey } from '@/lib/i18n/en'

interface EventFormModalProps {
  itemId: number
  onClose: () => void
  /** When provided, the modal edits this event instead of creating one. */
  event?: CalendarEvent
}

const EVENT_TYPES: EventType[] = ['watering', 'fertilizing', 'pruning', 'other']
const RECURRENCES: RecurrenceType[] = ['once', 'weekly', 'monthly', 'yearly']

// 'yearly' events repeat by definition, so the flag has nothing to toggle.
const SHOWS_REPEATS_CHECKBOX: RecurrenceType[] = ['once', 'weekly', 'monthly']

export function EventFormModal({ itemId, onClose, event }: EventFormModalProps) {
  const isEditing = !!event
  const createEvent = useCreateEvent(itemId)
  const updateEvent = useUpdateEvent()
  const { t } = useI18n()
  const isPending = createEvent.isPending || updateEvent.isPending

  const [title, setTitle] = useState(event?.title ?? '')
  const [description, setDescription] = useState(event?.description ?? '')
  const [date, setDate] = useState(event?.date ?? new Date().toISOString().split('T')[0])
  const [eventType, setEventType] = useState<EventType>(event?.event_type ?? 'other')
  const [recurrence, setRecurrence] = useState<RecurrenceType>(event?.recurrence ?? 'once')
  const [endDate, setEndDate] = useState(event?.end_date ?? '')
  const [repeatsYearly, setRepeatsYearly] = useState(event?.repeats_yearly ?? true)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = {
      item: event ? event.item : itemId,
      title,
      description,
      date,
      event_type: eventType,
      end_date: endDate || null,
      recurrence,
      repeats_yearly: repeatsYearly,
      is_manual: true,
    }
    if (isEditing) {
      await updateEvent.mutateAsync({ id: event!.id, data: payload })
    } else {
      await createEvent.mutateAsync(payload)
    }
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-800 rounded-t-2xl sm:rounded-2xl shadow-xl w-full max-w-md mx-0 sm:mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
            {isEditing ? t('addEventModal.editTitle') : t('addEventModal.title')}
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('addEventModal.titleLabel')}
            </label>
            <input
              required
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t('addEventModal.titlePlaceholder')}
              className="w-full rounded-lg border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('addEventModal.descriptionLabel')}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder={t('addEventModal.descriptionPlaceholder')}
              className="w-full rounded-lg border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('addEventModal.dateLabel')}
              </label>
              <input
                required
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full rounded-lg border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('addEventModal.typeLabel')}
              </label>
              <select
                value={eventType}
                onChange={(e) => setEventType(e.target.value as EventType)}
                className="w-full rounded-lg border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                {EVENT_TYPES.map((value) => (
                  <option key={value} value={value}>{t(`eventTypes.${value}` as TKey)}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('addEventModal.recurrenceLabel')}
            </label>
            <select
              value={recurrence}
              onChange={(e) => {
                const val = e.target.value as RecurrenceType
                setRecurrence(val)
                if (val === 'once') setEndDate('')
              }}
              className="w-full rounded-lg border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              {RECURRENCES.map((value) => (
                <option key={value} value={value}>{t(`recurrences.${value}` as TKey)}</option>
              ))}
            </select>
          </div>
          {recurrence !== 'once' && (
            <div>
              <label className="block text-sm font-medium text-gray-700
          dark:text-gray-300 mb-1">
                {t('addEventModal.endDateLabel')} <span className="text-gray-400 font-normal">{t('common.optional')}</span>
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                min={date}
                className="w-full rounded-lg border border-gray-200
          dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm
          text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2
          focus:ring-green-500"
              />
            </div>
          )}
          {SHOWS_REPEATS_CHECKBOX.includes(recurrence) && (
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
              <input
                type="checkbox"
                checked={repeatsYearly}
                onChange={(e) => setRepeatsYearly(e.target.checked)}
                className="rounded border-gray-300 dark:border-slate-600 text-green-600 focus:ring-green-500"
              />
              {t('addEventModal.repeatsYearly')}
            </label>
          )}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-200 dark:border-slate-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="flex-1 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              {isPending ? t('common.saving') : isEditing ? t('common.save') : t('addEventModal.addEvent')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
