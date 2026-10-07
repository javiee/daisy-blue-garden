'use client'

import { use, useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  RefreshCw,
  Leaf,
  Calendar,
  Plus,
  Pencil,
  Trash2,
  Check,
  X,
  Camera,
} from 'lucide-react'
import {
  useGardenItem,
  useItemEvents,
  useGenerateCare,
  usePatchGardenItem,
  usePatchGardenItemPhoto,
  useDeleteEvent,
} from '@/lib/hooks'
import { TypeBadge } from '@/components/TypeBadge'
import { EventCard } from '@/components/EventCard'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'
import { AddEventModal } from '@/components/AddEventModal'
import { useI18n } from '@/lib/i18n'

function InlineTextEdit({
  value,
  onSave,
  placeholder,
  rows = 4,
}: {
  value: string
  onSave: (v: string) => Promise<unknown>
  placeholder: string
  rows?: number
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  const [saving, setSaving] = useState(false)
  const { t } = useI18n()

  async function handleSave() {
    setSaving(true)
    await onSave(draft)
    setSaving(false)
    setEditing(false)
  }

  function handleCancel() {
    setDraft(value)
    setEditing(false)
  }

  if (editing) {
    return (
      <div className="space-y-2">
        <textarea
          autoFocus
          rows={rows}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="w-full rounded-lg border border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
        />
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-xs font-medium transition-colors disabled:opacity-50"
          >
            <Check className="w-3.5 h-3.5" />
            {saving ? t('common.saving') : t('common.save')}
          </button>
          <button
            onClick={handleCancel}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-600 text-gray-600 dark:text-gray-400 text-xs font-medium hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
            {t('common.cancel')}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="group relative">
      {value ? (
        <p className="text-gray-600 dark:text-gray-400 leading-relaxed text-sm">{value}</p>
      ) : (
        <p className="text-gray-400 italic text-sm">{placeholder}</p>
      )}
      <button
        onClick={() => { setDraft(value); setEditing(true) }}
        className="absolute -top-1 -right-1 p-2.5 rounded-md hover:bg-gray-100 dark:hover:bg-slate-600 transition-all text-gray-400 hover:text-gray-700"
        title={t('plantDetail.edit')}
      >
        <Pencil className="w-3.5 h-3.5 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200" />
      </button>
    </div>
  )
}

export default function PlantDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const itemId = Number(id)
  const photoInputRef = useRef<HTMLInputElement>(null)
  const { t } = useI18n()

  const [showAddEvent, setShowAddEvent] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [regenError, setRegenError] = useState<string | null>(null)
  const updatedAtAtStart = useRef<string | null>(null)
  const qc = useQueryClient()
  const { data: item, isLoading } = useGardenItem(itemId, regenerating ? 3000 : false)
  const { data: events } = useItemEvents(itemId)
  const generateCare = useGenerateCare()
  const patch = usePatchGardenItem(itemId)
  const patchPhoto = usePatchGardenItemPhoto(itemId)
  const deleteEvent = useDeleteEvent(itemId)

  // Stop "regenerating" when the LLM task saved new content (updated_at changed)
  useEffect(() => {
    if (!regenerating || !item) return
    if (updatedAtAtStart.current !== null && item.updated_at !== updatedAtAtStart.current) {
      setRegenerating(false)
      qc.invalidateQueries({ queryKey: ['events', 'item', itemId] })
    }
  }, [item, regenerating, qc, itemId])

  // Safety timeout: give up after 90s even if the task never updates the item
  useEffect(() => {
    if (!regenerating) return
    const timeout = setTimeout(() => setRegenerating(false), 90_000)
    return () => clearTimeout(timeout)
  }, [regenerating])

  if (isLoading) return <LoadingSkeleton />

  if (!item) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">{t('plantDetail.notFound')}</p>
      </div>
    )
  }

  function handlePhotoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) patchPhoto.mutate(file)
    // reset so re-selecting the same file still fires onChange
    e.target.value = ''
  }

  function handleRegenerate() {
    if (regenerating || generateCare.isPending) return
    setRegenError(null)
    updatedAtAtStart.current = item?.updated_at ?? null
    setRegenerating(true)
    generateCare.mutate(itemId, {
      onError: (err) => {
        setRegenError((err as Error)?.message ?? null)
        setRegenerating(false)
      },
    })
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-green-700 hover:text-green-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        {t('plantDetail.back')}
      </button>

      {/* Plant header */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg overflow-hidden">
        {/* Photo area */}
        <div className="relative group">
          {item.photo ? (
            <div className="relative h-64 w-full">
              <Image src={item.photo} alt={item.name} fill className="object-cover" />
            </div>
          ) : (
            <div className="h-48 bg-gradient-to-br from-green-100 to-emerald-200 dark:from-green-900 dark:to-emerald-800 flex items-center justify-center">
              <Leaf className="w-24 h-24 text-green-400 opacity-50" />
            </div>
          )}

          {/* Photo upload — desktop hover overlay */}
          <button
            onClick={() => photoInputRef.current?.click()}
            disabled={patchPhoto.isPending}
            className="absolute inset-0 hidden md:flex items-center justify-center bg-black/0 group-hover:bg-black/30 transition-colors cursor-pointer"
            title={item.photo ? t('plantDetail.replacePhoto') : t('plantDetail.uploadPhoto')}
          >
            <span className="flex flex-col items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity text-white">
              <Camera className="w-8 h-8 drop-shadow" />
              <span className="text-xs font-medium drop-shadow">
                {patchPhoto.isPending
                  ? t('plantDetail.uploading')
                  : item.photo
                    ? t('plantDetail.replacePhoto')
                    : t('plantDetail.uploadPhoto')}
              </span>
            </span>
          </button>

          {/* Photo upload — mobile always-visible button */}
          <button
            onClick={() => photoInputRef.current?.click()}
            disabled={patchPhoto.isPending}
            className="absolute top-2 right-2 p-2 rounded-full bg-black/50 text-white md:hidden disabled:opacity-50"
            title={item.photo ? t('plantDetail.replacePhoto') : t('plantDetail.uploadPhoto')}
          >
            <Camera className="w-5 h-5" />
          </button>

          <input
            ref={photoInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handlePhotoChange}
          />
        </div>

        <div className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">{item.name}</h1>
              <div className="mt-2"><TypeBadge type={item.type} /></div>
            </div>
            <button
              onClick={handleRegenerate}
              disabled={regenerating || generateCare.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-green-100 hover:bg-green-200 dark:bg-green-900 dark:hover:bg-green-800 text-green-800 dark:text-green-200 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${regenerating ? 'animate-spin' : ''}`} />
              {regenerating ? t('plantDetail.generating') : t('plantDetail.regenerateCare')}
            </button>
          </div>
          {regenerating && (
            <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
              {t('plantDetail.regenerating')}
            </p>
          )}
          {regenError && !regenerating && (
            <p className="mt-3 text-sm text-red-600 dark:text-red-400">
              {t('plantDetail.regenerateError')}
            </p>
          )}
        </div>
      </div>

      {/* Description & Care */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-3">{t('plantDetail.about')}</h2>
          <InlineTextEdit
            value={item.description}
            placeholder={t('plantDetail.aboutPlaceholder')}
            onSave={(description) => patch.mutateAsync({ description })}
          />
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">{t('plantDetail.careGuide')}</h2>
            {item.cares && (
              <button
                onClick={() => patch.mutate({ cares: '' })}
                disabled={patch.isPending}
                title={t('plantDetail.clearCareGuide')}
                className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
          <InlineTextEdit
            value={item.cares}
            placeholder={t('plantDetail.caresPlaceholder')}
            onSave={(cares) => patch.mutateAsync({ cares })}
          />
        </div>
      </div>

      {showAddEvent && (
        <AddEventModal itemId={itemId} onClose={() => setShowAddEvent(false)} />
      )}

      {/* Upcoming events */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-green-600" />
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
              {t('plantDetail.careSchedule')}
            </h2>
          </div>
          <button
            onClick={() => setShowAddEvent(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/40 hover:bg-green-100 dark:hover:bg-green-900 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            {t('plantDetail.addEvent')}
          </button>
        </div>
        {events && events.length > 0 ? (
          <div className="space-y-3">
            {events.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                onDelete={(id) => deleteEvent.mutateAsync(id)}
              />
            ))}
          </div>
        ) : (
          <p className="text-gray-400 italic text-center py-6">
            {t('plantDetail.noEvents')}
          </p>
        )}
      </div>
    </div>
  )
}
