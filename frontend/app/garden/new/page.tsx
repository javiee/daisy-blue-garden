'use client'

import { useRouter } from 'next/navigation'
import { PlantForm } from '@/components/PlantForm'

export default function NewPlantPage() {
  const router = useRouter()

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-green-800 dark:text-green-200">
          Add New Plant
        </h1>
        <p className="text-green-600 dark:text-green-400 mt-2">
          Add a plant or tree to your garden. AI will generate care recommendations automatically.
        </p>
      </div>
      <PlantForm
        onSuccess={(id) => router.push(`/garden/${id}`)}
        onCancel={() => router.back()}
      />
    </div>
  )
}
