'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Plus, Calendar, Bell, Settings } from 'lucide-react'
import { usePendingNotifications } from '@/lib/hooks'
import { cn } from '@/lib/utils'
import { useI18n } from '@/lib/i18n'
import type { TKey } from '@/lib/i18n/en'

const links: { href: string; key: TKey; icon: typeof Home }[] = [
  { href: '/', key: 'nav.garden', icon: Home },
  { href: '/garden/new', key: 'nav.addPlant', icon: Plus },
  { href: '/calendar', key: 'nav.calendar', icon: Calendar },
  { href: '/notifications', key: 'nav.notifications', icon: Bell },
  { href: '/settings', key: 'nav.settings', icon: Settings },
]

export function Navigation() {
  const pathname = usePathname()
  const { data: pending } = usePendingNotifications()
  const { t } = useI18n()
  const pendingCount = pending?.length ?? 0

  return (
    <nav className="hidden md:flex md:w-56 md:min-h-screen md:flex-col">
      {links.map(({ href, key, icon: Icon }) => {
        const isActive = pathname === href
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors',
              isActive
                ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                : 'text-gray-600 dark:text-gray-400 hover:bg-green-50 dark:hover:bg-slate-800'
            )}
          >
            <Icon className="w-5 h-5 flex-shrink-0" />
            <span>{t(key)}</span>
            {key === 'nav.notifications' && pendingCount > 0 && (
              <span className="ml-auto bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {pendingCount > 9 ? '9+' : pendingCount}
              </span>
            )}
          </Link>
        )
      })}
    </nav>
  )
}
