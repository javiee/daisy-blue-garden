'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from './api'

export function useGardenItems(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['garden', params],
    queryFn: () => api.garden.list(params),
  })
}

export function useGardenItem(id: number, refetchInterval?: number | false) {
  return useQuery({
    queryKey: ['garden', id],
    queryFn: () => api.garden.get(id),
    enabled: !!id,
    refetchInterval,
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

export function useIdentifyPlant() {
  return useMutation({
    mutationFn: (photo: File) => api.llm.identifyUpload(photo),
  })
}

export function useIdentification(id: number | null) {
  // Poll every 3s while the LLM is working; stop once complete or failed.
  // retry: false — a record deleted by the cleanup path 404s; retrying
  // those just adds log noise.
  return useQuery({
    queryKey: ['identification', id],
    queryFn: () => api.llm.identification(id!),
    enabled: !!id,
    retry: false,
    refetchInterval: (query) =>
      query.state.data?.status === 'pending' ? 3000 : false,
  })
}

export function useDeleteIdentification() {
  return useMutation({
    mutationFn: (id: number) => api.llm.deleteIdentification(id),
  })
}

export function useSendTestNotification() {
  return useMutation({
    mutationFn: (id: number) => api.notifications.testNotification(id),
  })
}

export function useAppSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => api.settings.get(),
  })
}

export function useSaveAppSettings() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<import('./types').AppSettings>) => api.settings.save(data),
    onSuccess: (updated) => qc.setQueryData(['settings'], updated),
  })
}