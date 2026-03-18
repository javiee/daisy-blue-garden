export function LoadingSkeleton() {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow overflow-hidden animate-pulse">
      <div className="h-44 bg-gray-200 dark:bg-slate-700" />
      <div className="p-4 space-y-3">
        <div className="h-5 bg-gray-200 dark:bg-slate-700 rounded-lg w-3/4" />
        <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded-lg w-1/2" />
        <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded-lg w-full" />
      </div>
    </div>
  )
}
