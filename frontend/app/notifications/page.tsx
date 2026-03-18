'use client'

import { useState } from 'react'
import { Bell, Settings } from 'lucide-react'
import { useNotifications, useAcknowledgeNotification, useNotificationConfig } from '@/lib/hooks'
import { NotificationItem } from '@/components/NotificationItem'
import { api } from '@/lib/api'
import type { NotificationFrequency } from '@/lib/types'

export default function NotificationsPage() {
  const { data: notifData, isLoading } = useNotifications()
  const { data: configData } = useNotificationConfig()
  const acknowledge = useAcknowledgeNotification()

  const [chatId, setChatId] = useState('')
  const [frequency, setFrequency] = useState<NotificationFrequency>('weekly')
  const [daysBefore, setDaysBefore] = useState(3)
  const [saving, setSaving] = useState(false)

  const notifications = notifData?.results ?? []
  const pending = notifications.filter((n) => !n.acknowledged)
  const acknowledged = notifications.filter((n) => n.acknowledged)
  const config = configData?.results?.[0]

  const handleSaveConfig = async () => {
    setSaving(true)
    try {
      await api.notifications.saveConfig({ telegram_chat_id: chatId, frequency, days_before: daysBefore })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="flex items-center gap-3">
        <Bell className="w-8 h-8 text-green-600" />
        <h1 className="text-3xl font-bold text-green-800 dark:text-green-200">Notifications</h1>
      </div>

      {/* Config section */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-6 space-y-4">
        <div className="flex items-center gap-2 mb-4">
          <Settings className="w-5 h-5 text-green-600" />
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
            Telegram Settings
          </h2>
        </div>
        {config && (
          <p className="text-sm text-green-600 dark:text-green-400">
            Current: Chat {config.telegram_chat_id} · {config.frequency} · {config.days_before} days before
          </p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Telegram Chat ID
            </label>
            <input
              type="text"
              value={chatId}
              onChange={(e) => setChatId(e.target.value)}
              placeholder="e.g. 123456789"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-700 text-gray-800 dark:text-gray-100 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Frequency
            </label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value as NotificationFrequency)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-700 text-gray-800 dark:text-gray-100 text-sm"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Days Before
            </label>
            <input
              type="number"
              min={1}
              max={30}
              value={daysBefore}
              onChange={(e) => setDaysBefore(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-700 text-gray-800 dark:text-gray-100 text-sm"
            />
          </div>
        </div>
        <button
          onClick={handleSaveConfig}
          disabled={saving || !chatId}
          className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>

      {/* Pending */}
      <div>
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-4">
          Pending ({pending.length})
        </h2>
        {isLoading ? (
          <p className="text-gray-400">Loading...</p>
        ) : pending.length === 0 ? (
          <div className="text-center py-8 bg-white dark:bg-slate-800 rounded-2xl shadow">
            <p className="text-gray-400">No pending notifications 🎉</p>
          </div>
        ) : (
          <div className="space-y-3">
            {pending.map((notif) => (
              <NotificationItem
                key={notif.id}
                notification={notif}
                onAcknowledge={() => acknowledge.mutate(notif.id)}
                isAcknowledging={acknowledge.isPending}
              />
            ))}
          </div>
        )}
      </div>

      {/* Acknowledged */}
      {acknowledged.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-600 dark:text-gray-400 mb-4">
            Acknowledged ({acknowledged.length})
          </h2>
          <div className="space-y-3 opacity-60">
            {acknowledged.slice(0, 10).map((notif) => (
              <NotificationItem
                key={notif.id}
                notification={notif}
                onAcknowledge={() => {}}
                isAcknowledging={false}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
