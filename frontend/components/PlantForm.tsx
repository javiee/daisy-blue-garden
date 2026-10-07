'use client'

import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, Sparkles, Upload } from 'lucide-react'
import { api } from '@/lib/api'
import {
  useCreateGardenItem,
  useDeleteIdentification,
  useIdentification,
  useIdentifyPlant,
} from '@/lib/hooks'
import type { GardenItemType } from '@/lib/types'
import { useI18n } from '@/lib/i18n'
import type { TKey } from '@/lib/i18n/en'

type FormData = {
  name: string
  type: GardenItemType
}

interface Props {
  onSuccess: (id: number) => void
  onCancel: () => void
}

const TYPE_EMOJI: Record<GardenItemType, string> = {
  plant: '🌿',
  tree: '🌳',
  shrub: '🌸',
  other: '🍀',
}

const IDENTIFY_TIMEOUT_MS = 90_000

export function PlantForm({ onSuccess, onCancel }: Props) {
  const { t } = useI18n()
  const [photo, setPhoto] = useState<File | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const create = useCreateGardenItem()

  // Photo identification state
  const [identificationId, setIdentificationId] = useState<number | null>(null)
  const [identifyError, setIdentifyError] = useState<string | null>(null)
  const [startedAt, setStartedAt] = useState<number | null>(null)
  const [draftDescription, setDraftDescription] = useState('')
  const [draftCares, setDraftCares] = useState('')

  const identify = useIdentifyPlant()
  const identification = useIdentification(identificationId)
  const deleteIdentification = useDeleteIdentification()
  const record = identification.data

  const schema = z.object({
    name: z.string().min(1, t('plantForm.nameRequired')).max(200),
    type: z.enum(['plant', 'tree', 'shrub', 'other']),
  })

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  const isIdentifying = identify.isPending || (record?.status === 'pending' && startedAt !== null)

  // Pre-fill the form once the LLM finishes (and clean up the record:
  // the browser still holds the original File, so nothing is lost).
  useEffect(() => {
    if (!record || startedAt === null) return
    if (record.status === 'complete' && record.name) {
      setValue('name', record.name)
      setValue('type', (record.type || 'plant') as GardenItemType)
      setDraftDescription(record.description)
      setDraftCares(record.cares)
      setIdentifyError(null)
      setIdentificationId(null)
      setStartedAt(null)
      deleteIdentification.mutate(record.id)
    } else if (record.status === 'failed') {
      setIdentifyError(record.error || t('plantForm.identifyFailedTitle'))
      setIdentificationId(null)
      setStartedAt(null)
      deleteIdentification.mutate(record.id)
    }
  }, [record, startedAt])

  // Give up after ~90s of pending (same as the rest of the app).
  useEffect(() => {
    if (startedAt === null || record?.status !== 'pending') return
    if (Date.now() - startedAt > IDENTIFY_TIMEOUT_MS) {
      setIdentifyError(t('plantForm.identifyTimeout'))
      setIdentificationId(null)
      setStartedAt(null)
      deleteIdentification.mutate(record.id)
    }
  }, [record, startedAt])

  // Clean up the record if the form unmounts while an identification is
  // in flight (Cancel / navigation) — otherwise the row and photo file
  // would be orphaned on the server.
  const inFlight = useRef<{ id: number | null; startedAt: number | null }>({ id: null, startedAt: null })
  inFlight.current = { id: identificationId, startedAt }
  useEffect(() => {
    return () => {
      const { id, startedAt: at } = inFlight.current
      if (id !== null && at !== null) {
        api.llm.deleteIdentification(id).catch(() => {})
      }
    }
  }, [])

  const handleIdentify = () => {
    if (!photo) return
    setIdentifyError(null)
    setDraftDescription('')
    setDraftCares('')
    setStartedAt(Date.now())
    identify.mutate(photo, {
      onSuccess: (rec) => setIdentificationId(rec.id),
      onError: (e) => {
        setIdentificationId(null)
        setStartedAt(null)
        setIdentifyError(e instanceof Error ? e.message : String(e))
      },
    })
  }

  const onSubmit = async (data: FormData) => {
    const formData = new FormData()
    formData.append('name', data.name)
    formData.append('type', data.type)
    if (draftDescription.trim()) formData.append('description', draftDescription.trim())
    if (draftCares.trim()) formData.append('cares', draftCares.trim())
    if (photo) formData.append('photo', photo)

    setIsGenerating(true)
    try {
      const item = await create.mutateAsync(formData)
      onSuccess(item.id)
    } catch (e) {
      setIsGenerating(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-8 space-y-6">
      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {t('plantForm.nameLabel')}
        </label>
        <input
          {...register('name')}
          type="text"
          placeholder={t('plantForm.namePlaceholder')}
          className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-slate-700 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-green-500 transition"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-500">{errors.name.message}</p>
        )}
      </div>

      {/* Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {t('plantForm.typeLabel')}
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {(['plant', 'tree', 'shrub', 'other'] as GardenItemType[]).map((type) => {
            return (
              <label key={type} className="cursor-pointer">
                <input {...register('type')} type="radio" value={type} className="sr-only peer" />
                <div className="text-center py-3 px-2 rounded-xl border-2 border-gray-200 dark:border-gray-600 peer-checked:border-green-500 peer-checked:bg-green-50 dark:peer-checked:bg-green-900 transition-all hover:border-green-300 text-sm font-medium text-gray-700 dark:text-gray-300">
                  {TYPE_EMOJI[type]} {t(`types.${type}` as TKey)}
                </div>
              </label>
            )
          })}
        </div>
        {errors.type && <p className="mt-1 text-sm text-red-500">{errors.type.message}</p>}
      </div>

      {/* Photo */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {t('plantForm.photoLabel')}
        </label>
        <label className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl cursor-pointer hover:border-green-400 transition-colors ${isIdentifying ? 'opacity-50 pointer-events-none' : ''}`}>
          <div className="flex flex-col items-center gap-2 text-gray-400">
            <Upload className="w-6 h-6" />
            <span className="text-sm">{photo ? photo.name : t('plantForm.uploadPhoto')}</span>
          </div>
          <input
            type="file"
            accept="image/*"
            className="hidden"
            disabled={isIdentifying}
            onChange={(e) => {
              // A new photo invalidates any AI draft from the previous one.
              setDraftDescription('')
              setDraftCares('')
              setPhoto(e.target.files?.[0] ?? null)
            }}
          />
        </label>

        {photo && (
          <div className="mt-3 space-y-2">
            <button
              type="button"
              onClick={handleIdentify}
              disabled={isIdentifying || isGenerating}
              className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isIdentifying
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Sparkles className="w-4 h-4" />}
              {t('plantForm.identifyButton')}
            </button>
            {!isIdentifying && (
              <p className="text-xs text-gray-500 dark:text-gray-400">{t('plantForm.identifyHint')}</p>
            )}
          </div>
        )}

        {isIdentifying && (
          <div className="mt-3 flex items-center gap-3 bg-purple-50 dark:bg-purple-950 border border-purple-200 dark:border-purple-800 rounded-xl p-4">
            <Loader2 className="w-5 h-5 text-purple-600 animate-spin" />
            <p className="text-sm text-purple-700 dark:text-purple-300">{t('plantForm.identifying')}</p>
          </div>
        )}

        {identifyError && (
          <div className="mt-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-xl p-4">
            <p className="text-sm font-medium text-red-700 dark:text-red-300">
              {t('plantForm.identifyFailedTitle')}
            </p>
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{identifyError}</p>
          </div>
        )}
      </div>

      {/* AI draft (after identification) */}
      {(draftDescription || draftCares) && (
        <div className="space-y-3">
          <p className="text-sm font-medium text-purple-700 dark:text-purple-300">
            {t('plantForm.aiDraftLabel')}
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('plantForm.descriptionLabel')}
            </label>
            <textarea
              value={draftDescription}
              onChange={(e) => setDraftDescription(e.target.value)}
              rows={3}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-slate-700 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 transition resize-y"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('plantForm.caresLabel')}
            </label>
            <textarea
              value={draftCares}
              onChange={(e) => setDraftCares(e.target.value)}
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-slate-700 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 transition resize-y"
            />
          </div>
        </div>
      )}

      {/* LLM notice */}
      <div className="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-xl p-4">
        <p className="text-sm text-green-700 dark:text-green-300">
          {t('plantForm.aiNotice')}
        </p>
      </div>

      {/* Generating state */}
      {isGenerating && (
        <div className="flex items-center gap-3 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
          <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
          <p className="text-sm text-blue-700 dark:text-blue-300">
            {t('plantForm.creating')}
          </p>
        </div>
      )}

      {/* Buttons */}
      <div className="flex gap-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-xl font-medium hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
        >
          {t('common.cancel')}
        </button>
        <button
          type="submit"
          disabled={create.isPending || isGenerating || isIdentifying}
          className="flex-1 py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {create.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
          {t('plantForm.addToGarden')}
        </button>
      </div>
    </form>
  )
}
