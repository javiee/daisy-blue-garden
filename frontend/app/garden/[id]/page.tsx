'use client'

import { use } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { ArrowLeft, RefreshCw, Leaf, Calendar } from 'lucide-react'
import { useGardenItem, useItemEvents, useGenerateCare } from '@/lib/hooks'
import { TypeBadge } from '@/components/TypeBadge'
import { EventCard } from '@/components/EventCard'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'

export default function PlantDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const itemId = Number(id)

  const { data: item, isLoading } = useGardenItem(itemId)
  const { data: events } = useItemEvents(itemId)
  const generateCare = useGenerateCare()

  if (isLoading) return <LoadingSkeleton />

  if (!item) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">Plant not found.</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-green-700 hover:text-green-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to garden
      </button>

      {/* Plant header */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg overflow-hidden">
        {item.photo ? (
          <div className="relative h-64 w-full">
            <Image src={item.photo} alt={item.name} fill className="object-cover" />
          </div>
        ) : (
          <div className="h-48 bg-gradient-to-br from-green-100 to-emerald-200 dark:from-green-900 dark:to-emerald-800 flex items-center justify-center">
            <Leaf className="w-24 h-24 text-green-400 opacity-50" />
          </div>
        )}
        <div className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">{item.name}</h1>
              <div className="mt-2"><TypeBadge type={item.type} /></div>
            </div>
            <button
              onClick={() => generateCare.mutate(itemId)}
              disabled={generateCare.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-green-100 hover:bg-green-200 dark:bg-green-900 dark:hover:bg-green-800 text-green-800 dark:text-green-200 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${generateCare.isPending ? 'animate-spin' : ''}`} />
              {generateCare.isPending ? 'Generating...' : 'Regenerate Care'}
            </button>
          </div>
        </div>
      </div>

      {/* Description & Care */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-3">About</h2>
          {item.description ? (
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{item.description}</p>
          ) : (
            <p className="text-gray-400 italic">AI is generating a description...</p>
          )}
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-3">Care Guide</h2>
          {item.cares ? (
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{item.cares}</p>
          ) : (
            <p className="text-gray-400 italic">AI is generating care instructions...</p>
          )}
        </div>
      </div>

      {/* Upcoming events */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-green-600" />
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
            Care Schedule
          </h2>
        </div>
        {events && events.length > 0 ? (
          <div className="space-y-3">
            {events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        ) : (
          <p className="text-gray-400 italic text-center py-6">
            No care events scheduled yet. AI will generate them shortly.
          </p>
        )}
      </div>
    </div>
  )
}
