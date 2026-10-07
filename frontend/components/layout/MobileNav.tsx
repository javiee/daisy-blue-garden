'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Plus, Calendar, Bell, Settings } from 'lucide-react'
import { usePendingNotifications } from '@/lib/hooks'
import { useI18n } from '@/lib/i18n'
import type { TKey } from '@/lib/i18n/en'

const links: { href: string; key: TKey; icon: typeof Home }[] = [
  { href: '/', key: 'nav.garden', icon: Home },
  { href: '/garden/new', key: 'nav.addPlant', icon: Plus },
  { href: '/calendar', key: 'nav.calendar', icon: Calendar },
  { href: '/notifications', key: 'nav.notifications', icon: Bell },
  { href: '/settings', key: 'nav.settings', icon: Settings },
]

export function MobileNav() {
  const pathname = usePathname()
  const { data: pending } = usePendingNotifications()
  const { t } = useI18n()
  const pendingCount = pending?.length ?? 0

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 flex bg-white dark:bg-slate-900 border-t border-green-100 dark:border-slate-700 md:hidden safe-area-pb">
      {links.map(({ href, key, icon: Icon }) => {
        const isActive = pathname === href
        return (
          <Link
            key={href}
            href={href}
            className={`flex-1 flex flex-col items-center py-2 gap-0.5 relative ${
              isActive
                ? 'text-green-700 dark:text-green-300'
                : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            <div className="relative">
              <Icon className="w-5 h-5" />
              {key === 'nav.notifications' && pendingCount > 0 && (
                <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-red-500" />
              )}
            </div>
            <span className="text-xs">{t(key)}</span>
          </Link>
        )
      })}
    </nav>
  )
}
