import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Pagination } from '../../components/ui/Pagination';
import { Badge } from '../../components/ui/Badge';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../components/ui/Toast';
import type { GdprRequest, PaginatedResponse } from '../../types';

const STATUS_BADGE: Record<string, string> = {
  pending: 'warning',
  processing: 'info',
  completed: 'success',
  failed: 'danger',
  cancelled: 'default',
};

const TYPE_BADGE: Record<string, string> = {
  export: 'info',
  anonymize: 'purple',
};

export default function GdprRequestsPage() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [showExport, setShowExport] = useState(false);
  const [showAnonymize, setShowAnonymize] = useState(false);
  const [targetEmail, setTargetEmail] = useState('');
  const [reason, setReason] = useState('');
  const pageSize = 20;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['gdpr-requests', page, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('page_size', String(pageSize));
      if (statusFilter) params.set('status', statusFilter);
      const resp = await api.get<PaginatedResponse<GdprRequest>>(`/audit/gdpr?${params}`);
      return resp.data;
    },
    refetchInterval: 10000,
  });

  const exportMutation = useMutation({
    mutationFn: async (email: string) => {
      const resp = await api.post('/audit/gdpr/export', { target_user_email: email });
      return resp.data;
    },
    onSuccess: () => {
      toast.success(t('gdpr.export_requested'));
      setShowExport(false);
      setTargetEmail('');
      queryClient.invalidateQueries({ queryKey: ['gdpr-requests'] });
    },
    onError: () => toast.error(t('gdpr.export_error')),
  });

  const anonymizeMutation = useMutation({
    mutationFn: async (params: { email: string; reason: string }) => {
      const resp = await api.post('/audit/gdpr/anonymize', {
        target_user_email: params.email,
        reason: params.reason,
      });
      return resp.data;
    },
    onSuccess: () => {
      toast.success(t('gdpr.anonymize_requested'));
      setShowAnonymize(false);
      setTargetEmail('');
      setReason('');
      queryClient.invalidateQueries({ queryKey: ['gdpr-requests'] });
    },
    onError: () => toast.error(t('gdpr.anonymize_error')),
  });

  const cancelMutation = useMutation({
    mutationFn: async (requestId: string) => {
      await api.post(`/audit/gdpr/${requestId}/cancel`);
    },
    onSuccess: () => {
      toast.success(t('gdpr.cancel_success'));
      queryClient.invalidateQueries({ queryKey: ['gdpr-requests'] });
    },
    onError: () => toast.error(t('gdpr.cancel_error')),
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error)?.message} onRetry={refetch} />;

  const requests = data?.data ?? [];
  const total = data?.meta?.total ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">{t('gdpr.title')}</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowExport(true)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {t('gdpr.export_data')}
          </button>
          <button
            onClick={() => setShowAnonymize(true)}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            {t('gdpr.anonymize_data')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">{t('gdpr.all_statuses')}</option>
          <option value="pending">{t('gdpr.status_pending')}</option>
          <option value="processing">{t('gdpr.status_processing')}</option>
          <option value="completed">{t('gdpr.status_completed')}</option>
          <option value="failed">{t('gdpr.status_failed')}</option>
          <option value="cancelled">{t('gdpr.status_cancelled')}</option>
        </select>
      </div>

      {/* Table */}
      {requests.length === 0 ? (
        <EmptyState message={t('gdpr.no_requests')} />
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">{t('gdpr.target_email')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">{t('gdpr.type')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">{t('gdpr.status')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">{t('gdpr.created_at')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">{t('gdpr.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {requests.map((req) => (
                <tr key={req.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{req.target_user_email}</td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <Badge variant={(TYPE_BADGE[req.request_type] || 'default') as 'info' | 'purple' | 'default'}>
                      {req.request_type}
                    </Badge>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <Badge variant={(STATUS_BADGE[req.status] || 'default') as 'warning' | 'info' | 'success' | 'danger' | 'default'}>
                      {req.status}
                    </Badge>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {req.created_at ? new Date(req.created_at).toLocaleString() : '-'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    {req.status === 'pending' && (
                      <button
                        onClick={() => cancelMutation.mutate(req.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        {t('gdpr.cancel')}
                      </button>
                    )}
                    {req.status === 'completed' && req.download_url && (
                      <a
                        href={req.download_url}
                        className="text-blue-600 hover:text-blue-800"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {t('gdpr.download')}
                      </a>
                    )}
                    {req.status === 'failed' && req.error_message && (
                      <span className="text-red-500" title={req.error_message}>
                        {t('gdpr.error')}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination page={page} pageSize={pageSize} total={total} onChange={setPage} />

      {/* Export Modal */}
      {showExport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-lg font-semibold">{t('gdpr.export_title')}</h2>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('gdpr.target_email')}</label>
            <input
              type="email"
              value={targetEmail}
              onChange={(e) => setTargetEmail(e.target.value)}
              className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              placeholder="user@example.com"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowExport(false); setTargetEmail(''); }}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={() => exportMutation.mutate(targetEmail)}
                disabled={!targetEmail || exportMutation.isPending}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {t('gdpr.request_export')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Anonymize Modal */}
      {showAnonymize && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-lg font-semibold">{t('gdpr.anonymize_title')}</h2>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('gdpr.target_email')}</label>
            <input
              type="email"
              value={targetEmail}
              onChange={(e) => setTargetEmail(e.target.value)}
              className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              placeholder="user@example.com"
            />
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('gdpr.reason')}</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="mb-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              rows={3}
              placeholder={t('gdpr.reason_placeholder')}
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowAnonymize(false); setTargetEmail(''); setReason(''); }}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={() => anonymizeMutation.mutate({ email: targetEmail, reason })}
                disabled={!targetEmail || !reason || anonymizeMutation.isPending}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {t('gdpr.request_anonymize')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
