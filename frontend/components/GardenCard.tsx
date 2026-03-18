import Link from 'next/link'
import Image from 'next/image'
import { Leaf } from 'lucide-react'
import type { GardenItem } from '@/lib/types'
import { TypeBadge } from './TypeBadge'

interface Props {
  item: GardenItem
}

export function GardenCard({ item }: Props) {
  return (
    <Link href={`/garden/${item.id}`} className="group block">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow hover:shadow-xl transition-all duration-300 overflow-hidden hover:-translate-y-1">
        {/* Photo */}
        <div className="relative h-44 overflow-hidden">
          {item.photo ? (
            <Image
              src={item.photo}
              alt={item.name}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-green-100 to-emerald-200 dark:from-green-900 dark:to-emerald-800 flex items-center justify-center">
              <Leaf className="w-16 h-16 text-green-400 opacity-60 group-hover:scale-110 transition-transform" />
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-4">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="font-semibold text-gray-800 dark:text-gray-100 text-lg leading-tight line-clamp-1">
              {item.name}
            </h3>
            <TypeBadge type={item.type} />
          </div>
          {item.description ? (
            <p className="text-gray-500 dark:text-gray-400 text-sm line-clamp-2 leading-relaxed">
              {item.description}
            </p>
          ) : (
            <p className="text-gray-400 dark:text-gray-500 text-sm italic">
              Generating care guide...
            </p>
          )}
        </div>
      </div>
    </Link>
  )
}
