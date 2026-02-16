import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import api from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { useToast } from '../../hooks/useToast';
import { formatDateTime } from '../../lib/date';
import { humanizeToken, useI18n } from '../../lib/i18n';
import type { ServiceRequest, Comment, Note } from '../../types';

export default function RequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, isRole } = useAuth();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const isTech = isRole('technician', 'admin', 'super_admin');

  const { data: request, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['request', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}`);
      return data.data as ServiceRequest;
    },
  });

  const { data: comments } = useQuery({
    queryKey: ['request-comments', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}/comments`);
      return data.data as Comment[];
    },
  });

  const { data: notes } = useQuery({
    queryKey: ['request-notes', id],
    queryFn: async () => {
      const { data } = await api.get(`/requests/${id}/notes`);
      return data.data as Note[];
    },
    enabled: isTech,
  });

  const [commentBody, setCommentBody] = useState('');
  const [noteBody, setNoteBody] = useState('');

  const addComment = useMutation({
    mutationFn: () => api.post(`/requests/${id}/comments`, { body: commentBody }),
    onSuccess: () => {
      setCommentBody('');
      queryClient.invalidateQueries({ queryKey: ['request-comments', id] });
      showToast({ title: t('page.request_detail.comment_added'), variant: 'success' });
    },
  });

  const addNote = useMutation({
    mutationFn: () => api.post(`/requests/${id}/notes`, { body: noteBody }),
    onSuccess: () => {
      setNoteBody('');
      queryClient.invalidateQueries({ queryKey: ['request-notes', id] });
      showToast({ title: t('page.request_detail.note_added'), variant: 'success' });
    },
  });

  const changeStatus = useMutation({
    mutationFn: (status: string) => api.patch(`/requests/${id}/status`, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request', id] });
      showToast({ title: t('page.request_detail.status_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.request_detail.error_generic');
      showToast({ title: t('page.request_detail.error_status_update'), description: detail, variant: 'error' });
    },
  });

  const changePriority = useMutation({
    mutationFn: (priority: string) => api.patch(`/requests/${id}/priority`, { priority }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request', id] });
      showToast({ title: t('page.request_detail.priority_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.request_detail.error_generic');
      showToast({ title: t('page.request_detail.error_priority_update'), description: detail, variant: 'error' });
    },
  });

  const assign = useMutation({
    mutationFn: () => api.patch(`/requests/${id}/assign`, { user_id: user?.id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['request', id] });
      showToast({ title: t('page.request_detail.assigned_to_you'), variant: 'success' });
    },
  });

  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <ErrorState
        message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }
  if (!request) return <ErrorState message={t('page.request_detail.not_found')} />;

  const statusActions: Record<string, string[]> = {
    submitted: ['in_review', 'rejected'],
    in_review: ['in_progress', 'rejected'],
    in_progress: ['resolved'],
    rejected: ['submitted'],
  };
  const nextStatuses = statusActions[request.status] || [];

  return (
    <div className="max-w-3xl space-y-6">
      <Card>
        <div className="flex items-start justify-between mb-4 gap-3">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{request.title}</h2>
            <div className="flex gap-2 mt-2">
              <StatusBadge status={request.status} />
              <StatusBadge status={request.priority} />
              <StatusBadge status={request.type} />
            </div>
          </div>

          {isTech && (
            <div>
              <label className="block text-xs text-gray-500 mb-1">{t('table.priority')}</label>
              <select
                value={request.priority}
                onChange={(e) => changePriority.mutate(e.target.value)}
                className="border rounded px-2 py-1 text-xs"
              >
                <option value="low">{t('enum.low')}</option>
                <option value="medium">{t('enum.medium')}</option>
                <option value="high">{t('enum.high')}</option>
                <option value="urgent">{t('enum.urgent')}</option>
              </select>
            </div>
          )}
        </div>

        <p className="text-sm text-gray-700 whitespace-pre-wrap mb-4">{request.description}</p>
        <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
          <div>{t('table.created')}: {formatDateTime(request.created_at)}</div>
          <div>{t('table.created_by')}: {request.created_by_email || request.created_by}</div>
          <div>{t('table.assigned_to')}: {request.assigned_to_email || request.assigned_to || t('common.unassigned')}</div>
        </div>

        {isTech && (
          <div className="flex gap-2 mt-4 flex-wrap">
            {!request.assigned_to && (
              <button onClick={() => assign.mutate()} className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700">
                {t('page.request_detail.assign_to_me')}
              </button>
            )}
            {nextStatuses.map((s) => (
              <button key={s} onClick={() => changeStatus.mutate(s)} className="border px-3 py-1.5 rounded text-sm hover:bg-gray-50">
                {t(`enum.${s}`, undefined, { defaultValue: humanizeToken(s) })}
              </button>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">{t('page.request_detail.comments')}</h3>
        <div className="space-y-3 mb-4">
          {comments?.map((c) => (
            <div key={c.id} className="bg-gray-50 rounded p-3">
              <p className="text-xs text-gray-500 mb-1">{c.author_email || c.author_id} &middot; {formatDateTime(c.created_at)}</p>
              <p className="text-sm text-gray-700">{c.body}</p>
            </div>
          ))}
          {!comments?.length && <p className="text-sm text-gray-400">{t('page.request_detail.no_comments')}</p>}
        </div>
        <div className="flex gap-2">
          <input
            value={commentBody}
            onChange={(e) => setCommentBody(e.target.value)}
            placeholder={t('page.request_detail.add_comment')}
            className="flex-1 border rounded px-3 py-1.5 text-sm"
          />
          <button onClick={() => addComment.mutate()} disabled={!commentBody.trim()} className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm disabled:opacity-50">
            {t('page.request_detail.send')}
          </button>
        </div>
      </Card>

      {isTech && (
        <Card>
          <h3 className="text-sm font-semibold text-gray-900 mb-3">{t('page.request_detail.internal_notes')}</h3>
          <div className="space-y-3 mb-4">
            {notes?.map((n) => (
              <div key={n.id} className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-xs text-gray-500 mb-1">{n.author_email || n.author_id} &middot; {formatDateTime(n.created_at)}</p>
                <p className="text-sm text-gray-700">{n.body}</p>
              </div>
            ))}
            {!notes?.length && <p className="text-sm text-gray-400">{t('page.request_detail.no_internal_notes')}</p>}
          </div>
          <div className="flex gap-2">
            <input
              value={noteBody}
              onChange={(e) => setNoteBody(e.target.value)}
              placeholder={t('page.request_detail.add_internal_note')}
              className="flex-1 border rounded px-3 py-1.5 text-sm"
            />
            <button onClick={() => addNote.mutate()} disabled={!noteBody.trim()} className="bg-yellow-600 text-white px-3 py-1.5 rounded text-sm disabled:opacity-50">
              {t('page.request_detail.add_note')}
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}
