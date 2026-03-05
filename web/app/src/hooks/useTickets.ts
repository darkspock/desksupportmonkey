import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';

export interface SupportTicket {
  id: string;
  reference: string;
  category: string;
  subject: string;
  status: string;
  priority: string;
  has_unread: boolean;
  created_at: string | null;
  updated_at: string | null;
  resolved_at: string | null;
}

export interface TicketMessage {
  id: string;
  author_id: string;
  author_name: string | null;
  author_email: string | null;
  body: string;
  is_from_platform: boolean;
  created_at: string | null;
}

export interface TicketDetail {
  id: string;
  reference: string;
  company_id: string;
  created_by: string;
  created_by_name: string | null;
  created_by_email: string | null;
  category: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  ai_conversation_summary: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  satisfaction_rating: number | null;
  satisfaction_comment: string | null;
  rated_at: string | null;
  messages: TicketMessage[];
}

interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
}

export function useMyTickets(page: number, status?: string) {
  return useQuery({
    queryKey: ['my-support-tickets', page, status],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (status) params.status = status;
      const { data } = await api.get('/my/support-tickets', { params });
      return data as { data: SupportTicket[]; meta: PaginationMeta };
    },
  });
}

export function useTicketDetail(ticketId: string) {
  return useQuery({
    queryKey: ['support-ticket', ticketId],
    queryFn: async () => {
      const { data } = await api.get(`/my/support-tickets/${ticketId}`);
      return data as { data: TicketDetail };
    },
    enabled: !!ticketId,
  });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      category: string;
      subject: string;
      description: string;
      ai_conversation_summary?: string;
    }) => {
      const { data } = await api.post('/my/support-tickets', body);
      return data as { data: TicketDetail };
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['my-support-tickets'] });
    },
  });
}

export function useAddMessage(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: string) => {
      await api.post(`/my/support-tickets/${ticketId}/messages`, { body });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['support-ticket', ticketId] });
    },
  });
}

export function useSubmitRating(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { rating: number; comment?: string }) => {
      const { data } = await api.post(`/my/support-tickets/${ticketId}/rating`, body);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['support-ticket', ticketId] });
      void queryClient.invalidateQueries({ queryKey: ['my-support-tickets'] });
    },
  });
}

export function useReopenTicket(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/my/support-tickets/${ticketId}/reopen`);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['support-ticket', ticketId] });
      void queryClient.invalidateQueries({ queryKey: ['my-support-tickets'] });
    },
  });
}
