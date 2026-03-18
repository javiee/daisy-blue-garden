'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, Upload } from 'lucide-react'
import { useCreateGardenItem } from '@/lib/hooks'
import type { GardenItemType } from '@/lib/types'

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(200),
  type: z.enum(['plant', 'tree', 'shrub', 'other']),
})

type FormData = z.infer<typeof schema>

interface Props {
  onSuccess: (id: number) => void
  onCancel: () => void
}

export function PlantForm({ onSuccess, onCancel }: Props) {
  const [photo, setPhoto] = useState<File | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const create = useCreateGardenItem()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormData) => {
    const formData = new FormData()
    formData.append('name', data.name)
    formData.append('type', data.type)
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
          Plant / Tree Name *
        </label>
        <input
          {...register('name')}
          type="text"
          placeholder="e.g. Red Rose, Oak Tree, Lavender"
          className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-slate-700 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-green-500 transition"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-500">{errors.name.message}</p>
        )}
      </div>

      {/* Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Type *
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {(['plant', 'tree', 'shrub', 'other'] as GardenItemType[]).map((type) => {
            const labels = { plant: '🌿 Plant', tree: '🌳 Tree', shrub: '🌸 Shrub', other: '🍀 Other' }
            return (
              <label key={type} className="cursor-pointer">
                <input {...register('type')} type="radio" value={type} className="sr-only peer" />
                <div className="text-center py-3 px-2 rounded-xl border-2 border-gray-200 dark:border-gray-600 peer-checked:border-green-500 peer-checked:bg-green-50 dark:peer-checked:bg-green-900 transition-all hover:border-green-300 text-sm font-medium text-gray-700 dark:text-gray-300">
                  {labels[type]}
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
          Photo (optional)
        </label>
        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl cursor-pointer hover:border-green-400 transition-colors">
          <div className="flex flex-col items-center gap-2 text-gray-400">
            <Upload className="w-6 h-6" />
            <span className="text-sm">{photo ? photo.name : 'Click to upload photo'}</span>
          </div>
          <input
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
          />
        </label>
      </div>

      {/* LLM notice */}
      <div className="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-xl p-4">
        <p className="text-sm text-green-700 dark:text-green-300">
          ✨ After adding, AI will automatically generate a description and care schedule for your plant.
        </p>
      </div>

      {/* Generating state */}
      {isGenerating && (
        <div className="flex items-center gap-3 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
          <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
          <p className="text-sm text-blue-700 dark:text-blue-300">
            Creating plant and generating AI care guide...
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
          Cancel
        </button>
        <button
          type="submit"
          disabled={create.isPending || isGenerating}
          className="flex-1 py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {create.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
          Add to Garden
        </button>
      </div>
    </form>
  )
}
