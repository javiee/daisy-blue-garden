'use client'

import { Check, Clock } from 'lucide-react'
import type { Notification } from '@/lib/types'
import { EventTypeIcon } from './EventTypeIcon'
import { formatDate } from '@/lib/utils'
import { useI18n } from '@/lib/i18n'

interface Props {
  notification: Notification
  onAcknowledge: () => void
  isAcknowledging: boolean
}

export function NotificationItem({ notification, onAcknowledge, isAcknowledging }: Props) {
  const { t, locale } = useI18n()
  const event = notification.event_detail

  return (
    <div className={`bg-white dark:bg-slate-800 rounded-xl shadow p-4 flex items-start gap-4 ${notification.acknowledged ? 'opacity-60' : ''}`}>
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2 flex-wrap">
          {event && <EventTypeIcon type={event.event_type} />}
          <span className="font-medium text-gray-800 dark:text-gray-100 text-sm">
            {event?.title ?? t('notificationItem.eventNumber', { id: notification.event })}
          </span>
        </div>
        {event && (
          <p className="text-xs text-gray-500 dark:text-gray-400">
            🌿 {event.item_detail?.name} · 📅 {formatDate(event.date, locale)}
          </p>
        )}
        {notification.sent_at && (
          <p className="text-xs text-gray-400 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {t('notificationItem.sentOn', { date: formatDate(notification.sent_at, locale) })}
          </p>
        )}
        {notification.acknowledged && notification.next_occurrence_date && (
          <p className="text-xs text-green-600 dark:text-green-400">
            {t('notificationItem.nextReminder', { date: formatDate(notification.next_occurrence_date, locale) })}
          </p>
        )}
      </div>
      {!notification.acknowledged && (
        <button
          onClick={onAcknowledge}
          disabled={isAcknowledging}
          className="flex-shrink-0 flex items-center gap-1.5 px-3 py-2.5 bg-green-100 hover:bg-green-200 dark:bg-green-900 dark:hover:bg-green-800 text-green-700 dark:text-green-300 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
        >
          <Check className="w-3.5 h-3.5" />
          {t('notificationItem.acknowledge')}
        </button>
      )}
    </div>
  )
}
