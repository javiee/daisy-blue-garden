'use client'

import Link from 'next/link'
import { Plus, Leaf } from 'lucide-react'
import { useGardenItems } from '@/lib/hooks'
import { GardenCard } from '@/components/GardenCard'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'

export default function HomePage() {
  const { data, isLoading, error } = useGardenItems()

  return (
    <div className="space-y-8">
      {/* Hero section */}
      <div className="text-center py-8">
        <div className="flex justify-center mb-4">
          <div className="p-4 bg-green-100 dark:bg-green-900 rounded-full">
            <Leaf className="w-12 h-12 text-green-600 dark:text-green-300" />
          </div>
        </div>
        <h1 className="text-4xl font-bold text-green-800 dark:text-green-200 mb-2">
          My Garden
        </h1>
        <p className="text-green-600 dark:text-green-400 text-lg">
          Your personal garden management companion
        </p>
      </div>

      {/* Add button */}
      <div className="flex justify-end">
        <Link
          href="/garden/new"
          className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-full font-semibold shadow-lg transition-all hover:shadow-xl hover:-translate-y-0.5"
        >
          <Plus className="w-5 h-5" />
          Add Plant
        </Link>
      </div>

      {/* Garden grid */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <LoadingSkeleton key={i} />
          ))}
        </div>
      )}

      {error && (
        <div className="text-center py-16">
          <p className="text-red-500 text-lg">Failed to load garden items.</p>
          <p className="text-gray-500 text-sm mt-2">Make sure the backend is running.</p>
        </div>
      )}

      {data && data.results.length === 0 && (
        <div className="text-center py-24">
          <div className="text-8xl mb-6">🌱</div>
          <h2 className="text-2xl font-semibold text-green-700 dark:text-green-300 mb-3">
            Your garden is empty
          </h2>
          <p className="text-green-600 dark:text-green-400 mb-8 text-lg">
            Add your first plant or tree to get started!
          </p>
          <Link
            href="/garden/new"
            className="inline-flex items-center gap-2 px-8 py-4 bg-green-600 hover:bg-green-700 text-white rounded-full font-semibold shadow-lg text-lg transition-all"
          >
            <Plus className="w-6 h-6" />
            Add your first plant
          </Link>
        </div>
      )}

      {data && data.results.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {data.results.map((item) => (
            <GardenCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}
