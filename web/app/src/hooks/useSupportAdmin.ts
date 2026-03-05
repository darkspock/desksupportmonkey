import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { TicketDetail } from './useTickets';

export interface SupportAdminTicket {
  id: string;
  reference: string;
  category: string;
  subject: string;
  status: string;
  priority: string;
  has_unread: boolean;
  company_id: string | null;
  created_by_email: string | null;
  created_at: string | null;
  updated_at: string | null;
  resolved_at: string | null;
}

export interface TicketStats {
  open: number;
  in_progress: number;
  waiting_on_customer: number;
  resolved: number;
  closed: number;
  total: number;
  avg_satisfaction_rating: number | null;
}

interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
}

interface SupportTicketsParams {
  page: number;
  status?: string;
  priority?: string;
  category?: string;
  search?: string;
  company_id?: string;
  sort_by?: string;
  sort_order?: string;
}

export function useSupportTickets(params: SupportTicketsParams) {
  return useQuery({
    queryKey: ['support-admin-tickets', params],
    queryFn: async () => {
      const queryParams: Record<string, unknown> = { page: params.page, page_size: 20 };
      if (params.status) queryParams.status = params.status;
      if (params.priority) queryParams.priority = params.priority;
      if (params.category) queryParams.category = params.category;
      if (params.search) queryParams.search = params.search;
      if (params.company_id) queryParams.company_id = params.company_id;
      if (params.sort_by) queryParams.sort_by = params.sort_by;
      if (params.sort_order) queryParams.sort_order = params.sort_order;
      const { data } = await api.get('/support-tickets', { params: queryParams });
      return data as { data: SupportAdminTicket[]; meta: PaginationMeta };
    },
  });
}

export function useSupportTicketStats() {
  return useQuery({
    queryKey: ['support-admin-ticket-stats'],
    queryFn: async () => {
      const { data } = await api.get('/support-tickets/stats');
      return data as { data: TicketStats };
    },
  });
}

export function useSupportTicketDetail(ticketId: string) {
  return useQuery({
    queryKey: ['support-admin-ticket', ticketId],
    queryFn: async () => {
      const { data } = await api.get(`/support-tickets/${ticketId}`);
      return data as { data: TicketDetail };
    },
    enabled: !!ticketId,
  });
}

export function useAddPlatformMessage(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: string) => {
      await api.post(`/support-tickets/${ticketId}/messages`, { body });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['support-admin-ticket', ticketId] });
      void queryClient.invalidateQueries({ queryKey: ['support-admin-tickets'] });
    },
  });
}

export function useChangeTicketStatus(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (status: string) => {
      const { data } = await api.patch(`/support-tickets/${ticketId}/status`, { status });
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['support-admin-ticket', ticketId] });
      void queryClient.invalidateQueries({ queryKey: ['support-admin-tickets'] });
      void queryClient.invalidateQueries({ queryKey: ['support-admin-ticket-stats'] });
    },
  });
}

export function useChangeTicketPriority(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (priority: string) => {
      const { data } = await api.patch(`/support-tickets/${ticketId}/priority`, { priority });
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['support-admin-ticket', ticketId] });
      void queryClient.invalidateQueries({ queryKey: ['support-admin-tickets'] });
    },
  });
}
