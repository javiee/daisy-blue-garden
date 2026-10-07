'use client'

import type { GardenItemType } from '@/lib/types'
import { cn } from '@/lib/utils'
import { useI18n } from '@/lib/i18n'
import type { TKey } from '@/lib/i18n/en'

const CONFIG: Record<GardenItemType, { emoji: string; className: string }> = {
  plant: { emoji: '🌿', className: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
  tree: { emoji: '🌳', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300' },
  shrub: { emoji: '🌸', className: 'bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300' },
  other: { emoji: '🍀', className: 'bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300' },
}

export function TypeBadge({ type }: { type: GardenItemType }) {
  const { t } = useI18n()
  const config = CONFIG[type] ?? CONFIG.other
  return (
    <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', config.className)}>
      <span>{config.emoji}</span>
      {t(`types.${type}` as TKey)}
    </span>
  )
}
