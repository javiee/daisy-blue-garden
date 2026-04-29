'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from './api'

export function useGardenItems(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['garden', params],
    queryFn: () => api.garden.list(params),
  })
}

export function useGardenItem(id: number) {
  return useQuery({
    queryKey: ['garden', id],
    queryFn: () => api.garden.get(id),
    enabled: !!id,
  })
}

export function useCreateGardenItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: FormData) => api.garden.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['garden'] }),
  })
}

export function usePatchGardenItem(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<import('./types').GardenItem>) => api.garden.patch(id, data),
    onSuccess: (updated) => {
      qc.setQueryData(['garden', id], updated)
      qc.invalidateQueries({ queryKey: ['garden'] })
    },
  })
}

export function usePatchGardenItemPhoto(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (photo: File) => api.garden.patchPhoto(id, photo),
    onSuccess: (updated) => {
      qc.setQueryData(['garden', id], updated)
      qc.invalidateQueries({ queryKey: ['garden'] })
    },
  })
}

export function useDeleteGardenItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.garden.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['garden'] }),
  })
}

export function useCalendarEvents(params?: { week?: string; month?: string; item?: number }) {
  return useQuery({
    queryKey: ['events', params],
    queryFn: () => api.events.list(params),
  })
}

export function useItemEvents(itemId: number, baseOnly = true) {
  return useQuery({
    queryKey: ['events', 'item', itemId, { baseOnly }],
    queryFn: () => api.events.byItem(itemId, baseOnly ? { base_only: 'true' } : undefined),
    enabled: !!itemId,
  })
}

export function useDeleteEvent(itemId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (eventId: number) => api.events.delete(eventId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['events', 'item', itemId] }),
  })
}

export function useCreateEvent(itemId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Omit<import('./types').CalendarEvent, 'id' | 'item_detail' | 'created_at' | 'parent_event'>) =>
      api.events.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['events', 'item', itemId] }),
  })
}

export function usePendingNotifications() {
  return useQuery({
    queryKey: ['notifications', 'pending'],
    queryFn: () => api.notifications.pending(),
    refetchInterval: 60_000, // poll every minute
  })
}

export function useNotifications() {
  return useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.notifications.list(),
  })
}

export function useAcknowledgeNotification() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.notifications.acknowledge(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}

export function useNotificationConfig() {
  return useQuery({
    queryKey: ['notifications', 'config'],
    queryFn: () => api.notifications.getConfig(),
  })
}

export function useGenerateCare() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (itemId: number) => api.llm.generateCare(itemId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['garden'] }),
  })
}

export function useSendTestNotification() {
  return useMutation({
    mutationFn: (id: number) => api.notifications.testNotification(id),
  })
}