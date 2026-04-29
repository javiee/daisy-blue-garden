import Link from 'next/link'
import { Flower2 } from 'lucide-react'

export function Header() {
  return (
    <header className="bg-white dark:bg-slate-900 border-b border-green-100 dark:border-slate-700 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="p-2 bg-green-100 dark:bg-green-900 rounded-xl group-hover:bg-green-200 transition-colors">
            <Flower2 className="w-6 h-6 text-green-600 dark:text-green-300" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-green-800 dark:text-green-200 leading-tight">
              DaisyBlue
            </h1>
            <p className="text-xs text-green-500 dark:text-green-400 leading-tight">Gardener</p>
          </div>
        </Link>
        <div className="hidden sm:block text-sm text-green-600 dark:text-green-400">
          AI-powered garden care
        </div>
      </div>
    </header>
  )
}
