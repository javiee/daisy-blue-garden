'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Plus, Calendar, Bell } from 'lucide-react'
import { usePendingNotifications } from '@/lib/hooks'
import { cn } from '@/lib/utils'

const links = [
  { href: '/', label: 'Garden', icon: Home },
  { href: '/garden/new', label: 'Add Plant', icon: Plus },
  { href: '/calendar', label: 'Calendar', icon: Calendar },
  { href: '/notifications', label: 'Notifications', icon: Bell },
]

export function Navigation() {
  const pathname = usePathname()
  const { data: pending } = usePendingNotifications()
  const pendingCount = pending?.length ?? 0

  return (
    <nav className="w-56 min-h-screen bg-white dark:bg-slate-900 border-r border-green-100 dark:border-slate-700 p-4 space-y-1">
      {links.map(({ href, label, icon: Icon }) => {
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
            <span>{label}</span>
            {label === 'Notifications' && pendingCount > 0 && (
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
