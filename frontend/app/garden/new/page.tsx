'use client'

import { useRouter } from 'next/navigation'
import { PlantForm } from '@/components/PlantForm'
import { useI18n } from '@/lib/i18n'

export default function NewPlantPage() {
  const router = useRouter()
  const { t } = useI18n()

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-green-800 dark:text-green-200">
          {t('newPlant.title')}
        </h1>
        <p className="text-green-600 dark:text-green-400 mt-2">
          {t('newPlant.subtitle')}
        </p>
      </div>
      <PlantForm
        onSuccess={(id) => router.push(`/garden/${id}`)}
        onCancel={() => router.back()}
      />
    </div>
  )
}
