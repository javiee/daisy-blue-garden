'use client'

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { en, type Locale, type TKey, type TranslationDict } from './en'
import { es } from './es'
import { API_BASE } from '@/lib/api'

const STORAGE_KEY = 'daisyblue.locale'
const DICTS: Record<Locale, TranslationDict> = { en, es }

interface I18nContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: TKey, vars?: Record<string, string | number>) => string
}

function lookup(dict: TranslationDict, key: TKey): string | undefined {
  const value = key
    .split('.')
    .reduce<unknown>((acc, part) => (acc as Record<string, unknown>)?.[part], dict)
  return typeof value === 'string' ? value : undefined
}

function detectLocale(): Locale {
  const saved = window.localStorage.getItem(STORAGE_KEY)
  if (saved === 'en' || saved === 'es') return saved
  return navigator.language.toLowerCase().startsWith('es') ? 'es' : 'en'
}

const I18nContext = createContext<I18nContextValue>({
  locale: 'en',
  setLocale: () => {},
  t: (key) => lookup(en, key) ?? key,
})

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('en')

  useEffect(() => {
    let cancelled = false
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved === 'en' || saved === 'es') {
      setLocaleState(saved)
      return
    }
    // No stored preference: ask the backend, then fall back to browser language
    fetch(`${API_BASE}/settings/`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled) return
        if (data?.language === 'en' || data?.language === 'es') {
          setLocaleState(data.language)
        } else {
          setLocaleState(navigator.language.toLowerCase().startsWith('es') ? 'es' : 'en')
        }
      })
      .catch(() => {
        if (!cancelled) {
          setLocaleState(navigator.language.toLowerCase().startsWith('es') ? 'es' : 'en')
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    document.documentElement.lang = locale
  }, [locale])

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next)
    window.localStorage.setItem(STORAGE_KEY, next)
  }, [])

  const t = useCallback(
    (key: TKey, vars?: Record<string, string | number>) => {
      let text = lookup(DICTS[locale], key) ?? lookup(DICTS.en, key) ?? key
      if (vars) {
        for (const [name, value] of Object.entries(vars)) {
          text = text.replace(new RegExp(`{{${name}}}`, 'g'), String(value))
        }
      }
      return text
    },
    [locale]
  )

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t])
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nContextValue {
  return useContext(I18nContext)
}
