import type { GardenItemType } from '@/lib/types'
import { cn } from '@/lib/utils'

const CONFIG: Record<GardenItemType, { label: string; emoji: string; className: string }> = {
  plant: { label: 'Plant', emoji: '🌿', className: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' },
  tree: { label: 'Tree', emoji: '🌳', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300' },
  shrub: { label: 'Shrub', emoji: '🌸', className: 'bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300' },
  other: { label: 'Other', emoji: '🍀', className: 'bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300' },
}

export function TypeBadge({ type }: { type: GardenItemType }) {
  const config = CONFIG[type] ?? CONFIG.other
  return (
    <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', config.className)}>
      <span>{config.emoji}</span>
      {config.label}
    </span>
  )
}
