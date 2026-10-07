'use client'

import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Languages, Check, Sprout, RotateCcw } from 'lucide-react'
import { useAppSettings, useSaveAppSettings } from '@/lib/hooks'
import { useI18n } from '@/lib/i18n'
import type { Locale } from '@/lib/i18n/en'

const LOCALES: { value: Locale; labelKey: 'settings.english' | 'settings.spanish' }[] = [
  { value: 'en', labelKey: 'settings.english' },
  { value: 'es', labelKey: 'settings.spanish' },
]

export default function SettingsPage() {
  const { t, locale, setLocale } = useI18n()
  const save = useSaveAppSettings()
  const { data: settings } = useAppSettings()
  const [justSaved, setJustSaved] = useState(false)
  const [prompt, setPrompt] = useState('')

  useEffect(() => {
    if (settings) setPrompt(settings.gardener_prompt)
  }, [settings])

  function handleSelect(next: Locale) {
    if (next === locale) return
    setLocale(next)
    setJustSaved(false)
    save.mutate(
      { language: next },
      {
        onSuccess: () => {
          setJustSaved(true)
          setTimeout(() => setJustSaved(false), 3000)
        },
      }
    )
  }

  function handleSavePrompt() {
    setJustSaved(false)
    save.mutate(
      { gardener_prompt: prompt },
      {
        onSuccess: () => {
          setJustSaved(true)
          setTimeout(() => setJustSaved(false), 3000)
        },
      }
    )
  }

  function handleResetPrompt() {
    setPrompt('')
    setJustSaved(false)
    save.mutate(
      { gardener_prompt: '' },
      {
        onSuccess: () => {
          setJustSaved(true)
          setTimeout(() => setJustSaved(false), 3000)
        },
      }
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="flex items-center gap-3">
        <SettingsIcon className="w-8 h-8 text-green-600" />
        <h1 className="text-3xl font-bold text-green-800 dark:text-green-200">
          {t('settings.title')}
        </h1>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Languages className="w-5 h-5 text-green-600" />
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
            {t('settings.language')}
          </h2>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">{t('settings.languageHint')}</p>
        <div className="flex gap-3">
          {LOCALES.map(({ value, labelKey }) => (
            <button
              key={value}
              onClick={() => handleSelect(value)}
              className={`flex items-center gap-2 px-5 py-3 rounded-lg text-sm font-medium border transition-colors ${
                locale === value
                  ? 'bg-green-600 border-green-600 text-white'
                  : 'bg-white dark:bg-slate-700 border-gray-200 dark:border-slate-600 text-gray-700 dark:text-gray-200 hover:bg-green-50 dark:hover:bg-slate-600'
              }`}
            >
              {locale === value && <Check className="w-4 h-4" />}
              {t(labelKey)}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sprout className="w-5 h-5 text-green-600" />
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
              {t('settings.gardenerPrompt')}
            </h2>
          </div>
          {prompt.trim() && (
            <button
              onClick={handleResetPrompt}
              disabled={save.isPending}
              className="flex items-center gap-1 text-sm text-gray-500 hover:text-red-500 dark:text-gray-400 transition-colors disabled:opacity-50"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              {t('settings.gardenerPromptReset')}
            </button>
          )}
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t('settings.gardenerPromptHint')}
        </p>
        <textarea
          rows={5}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={t('settings.gardenerPromptPlaceholder')}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-700 text-gray-800 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 resize-y"
        />
        <div className="flex items-center gap-3">
          <button
            onClick={handleSavePrompt}
            disabled={save.isPending || prompt === (settings?.gardener_prompt ?? '')}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {save.isPending ? t('common.saving') : t('common.save')}
          </button>
          {save.isError && (
            <p className="text-sm text-red-600 dark:text-red-400">
              {(save.error as Error)?.message}
            </p>
          )}
          {justSaved && !save.isPending && (
            <p className="text-sm text-green-600 dark:text-green-400">
              {t('settings.saved')}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
