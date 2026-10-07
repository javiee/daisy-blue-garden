import { describe, it, expect } from 'vitest'
import { en } from '@/lib/i18n/en'
import { es } from '@/lib/i18n/es'

function flattenKeys(obj: Record<string, unknown>, prefix = ''): string[] {
  return Object.entries(obj).flatMap(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key
    if (value !== null && typeof value === 'object') {
      return flattenKeys(value as Record<string, unknown>, path)
    }
    return [path]
  })
}

describe('i18n dictionaries', () => {
  it('es has the exact same keys as en', () => {
    const enKeys = flattenKeys(en).sort()
    const esKeys = flattenKeys(es).sort()
    expect(esKeys).toEqual(enKeys)
  })

  it('es has no empty string values', () => {
    for (const key of flattenKeys(es)) {
      const value = key.split('.').reduce<unknown>((acc, part) => {
        const next = (acc as Record<string, unknown>)?.[part]
        return next
      }, es)
      expect(typeof value, `es.${key}`).toBe('string')
      expect((value as string).length, `es.${key}`).toBeGreaterThan(0)
    }
  })

  it('es does not accidentally equal en for long strings', () => {
    const enMap = new Map<string, string>(
      flattenKeys(en).map((k) => [k, getValue(en, k)])
    )
    const esMap = new Map<string, string>(
      flattenKeys(es).map((k) => [k, getValue(es, k)])
    )
    const identical = [...enMap.entries()].filter(([k, v]) => {
      const esValue = esMap.get(k)
      // Short words like 'Edit', 'Month', 'Cancel' are legitimately identical
      return esValue === v && v.length > 12
    })
    expect(identical).toEqual([])
  })
})

function getValue(obj: Record<string, unknown>, key: string): string {
  return key.split('.').reduce<unknown>((acc, part) => {
    return (acc as Record<string, unknown>)?.[part]
  }, obj) as string
}
