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

export function useItemEvents(itemId: number) {
  return useQuery({
    queryKey: ['events', 'item', itemId],
    queryFn: () => api.events.byItem(itemId),
    enabled: !!itemId,
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
