import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Pagination } from '../../components/ui/Pagination';
import { Badge } from '../../components/ui/Badge';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../components/ui/Toast';
import type { AuditEntry, PaginatedResponse } from '../../types';

const HTTP_BADGE: Record<string, string> = {
  GET: 'info', POST: 'success', PUT: 'warning', PATCH: 'warning', DELETE: 'danger',
};

const RETENTION_OPTIONS = [
  { value: 0, labelKey: 'audit.retention.indefinite' },
  { value: 12, labelKey: 'audit.retention.months_1y' },
  { value: 24, labelKey: 'audit.retention.months_2y' },
  { value: 36, labelKey: 'audit.retention.months_3y' },
  { value: 60, labelKey: 'audit.retention.months_5y' },
  { value: 84, labelKey: 'audit.retention.months_7y' },
];

export default function AuditLogPage() {
  const { t } = useI18n();
  const toast = useToast();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [action, setAction] = useState('');
  const [resourceType, setResourceType] = useState('');
  const [showExport, setShowExport] = useState(false);
  const [exportFormat, setExportFormat] = useState('csv');
  const [retentionMonths, setRetentionMonths] = useState(36);
  const [verifyTaskId, setVerifyTaskId] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<{
    status: string;
    total_checked?: number;
    valid_count?: number;
    invalid_count?: number;
    first_invalid_entry_id?: string;
  } | null>(null);
  const pageSize = 20;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['audit-entries', page, search, action, resourceType],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (search) params.search = search;
      if (action) params.action = action;
      if (resourceType) params.resource_type = resourceType;
      const { data } = await api.get('/audit', { params });
      return data as PaginatedResponse<AuditEntry>;
    },
  });

  // Retention policy
  const retentionQuery = useQuery({
    queryKey: ['audit-retention'],
    queryFn: async () => {
      const { data } = await api.get('/audit/retention');
      return data as { retention_months: number; updated_at: string | null; updated_by: string | null };
    },
  });

  useEffect(() => {
    if (retentionQuery.data) {
      setRetentionMonths(retentionQuery.data.retention_months);
    }
  }, [retentionQuery.data]);

  const retentionMutation = useMutation({
    mutationFn: async (months: number) => {
      await api.put('/audit/retention', { retention_months: months });
    },
    onSuccess: () => {
      toast.success(t('audit.retention.updated'));
      retentionQuery.refetch();
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      toast.error(message);
    },
  });

  // Export
  const exportMutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, unknown> = { format: exportFormat };
      if (action) body.action = action;
      if (resourceType) body.resource_type = resourceType;
      if (search) body.search = search;
      const { data } = await api.post('/audit/export', body);
      return data as { task_id: string };
    },
    onSuccess: () => {
      toast.success(t('audit.export.requested'));
      setShowExport(false);
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      toast.error(message);
    },
  });

  // Integrity verification
  const verifyMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/audit/verify', {});
      return data as { task_id: string };
    },
    onSuccess: (result) => {
      setVerifyTaskId(result.task_id);
      setVerifyResult(null);
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      toast.error(message);
    },
  });

  // Poll verify task status
  useEffect(() => {
    if (!verifyTaskId) return;
    const interval = setInterval(async () => {
      try {
        const { data } = await api.get(`/audit/verify/${verifyTaskId}`);
        if (data.status === 'completed' || data.status === 'failed') {
          setVerifyResult(data);
          setVerifyTaskId(null);
        }
      } catch {
        setVerifyTaskId(null);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [verifyTaskId]);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString();
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('audit.log.title')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('audit.log.subtitle')}</p>
        </div>
        <button
          onClick={() => setShowExport(true)}
          className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          {t('audit.export.button')}
        </button>
      </div>

      {/* Retention & Integrity Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Retention Policy Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">{t('audit.retention.title')}</h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">{t('audit.retention.description')}</p>
          <div className="flex items-center gap-3">
            <select
              value={retentionMonths}
              onChange={(e) => setRetentionMonths(Number(e.target.value))}
              className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
            >
              {RETENTION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{t(opt.labelKey)}</option>
              ))}
            </select>
            <button
              onClick={() => retentionMutation.mutate(retentionMonths)}
              disabled={retentionMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {retentionMutation.isPending ? t('common.saving') : t('common.save')}
            </button>
          </div>
          {retentionMonths > 0 && retentionMonths < 24 && (
            <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">{t('audit.retention.warning')}</p>
          )}
        </div>

        {/* Integrity Verification Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">{t('audit.verify.title')}</h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">{t('audit.verify.description')}</p>
          <button
            onClick={() => verifyMutation.mutate()}
            disabled={verifyMutation.isPending || !!verifyTaskId}
            className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50"
          >
            {verifyTaskId ? t('audit.verify.running') : t('audit.verify.button')}
          </button>
          {verifyResult && verifyResult.status === 'completed' && (
            <div className="mt-3 text-sm">
              <div className="flex gap-4">
                <span className="text-gray-600 dark:text-gray-400">{t('audit.verify.total_checked')}: <span className="font-medium text-gray-900 dark:text-white">{verifyResult.total_checked}</span></span>
                <span className="text-green-600">{t('audit.verify.valid')}: {verifyResult.valid_count}</span>
                {(verifyResult.invalid_count ?? 0) > 0 && (
                  <span className="text-red-600">{t('audit.verify.invalid')}: {verifyResult.invalid_count}</span>
                )}
              </div>
              {verifyResult.invalid_count === 0 && (
                <p className="text-green-600 mt-1">{t('audit.verify.all_valid')}</p>
              )}
              {(verifyResult.invalid_count ?? 0) > 0 && (
                <p className="text-red-600 mt-1">{t('audit.verify.tampering_detected')} {verifyResult.first_invalid_entry_id}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder={t('audit.log.search_placeholder')}
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm w-64"
        />
        <input
          type="text"
          placeholder={t('audit.log.filter_action')}
          value={action}
          onChange={(e) => { setAction(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm w-48"
        />
        <input
          type="text"
          placeholder={t('audit.log.filter_resource_type')}
          value={resourceType}
          onChange={(e) => { setResourceType(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm w-48"
        />
      </div>

      {/* Export Modal */}
      {showExport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 w-96">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('audit.export.title')}</h2>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('audit.export.format')}</label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
              >
                <option value="csv">CSV</option>
                <option value="pdf">PDF</option>
              </select>
            </div>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowExport(false)} className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                {t('common.cancel')}
              </button>
              <button
                onClick={() => exportMutation.mutate()}
                disabled={exportMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {exportMutation.isPending ? t('common.working') : t('audit.export.start')}
              </button>
            </div>
          </div>
        </div>
      )}

      {isLoading && <Loading />}
      {isError && <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />}
      {data && data.data.length === 0 && <EmptyState title={t('audit.log.no_entries')} />}

      {data && data.data.length > 0 && (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_timestamp')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_actor')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_method')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_action')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_resource')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_status')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_ip')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.log.col_tags')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {data.data.map((entry) => (
                  <tr
                    key={entry.id}
                    onClick={() => navigate(`/audit/${entry.id}`)}
                    className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
                      {formatDate(entry.created_at)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white truncate max-w-[200px]">
                      {entry.actor_email}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <Badge variant={HTTP_BADGE[entry.http_method] || 'default'}>{entry.http_method}</Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {entry.action}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      <span className="font-medium">{entry.resource_type}</span>
                      {entry.resource_id && (
                        <span className="ml-1 text-gray-400 dark:text-gray-500 text-xs">{entry.resource_id.slice(0, 12)}...</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <Badge variant={entry.response_status < 400 ? 'success' : entry.response_status < 500 ? 'warning' : 'danger'}>
                        {entry.response_status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {entry.ip_address || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {entry.tag_count > 0 && (
                        <Badge variant="purple">{entry.tag_count}</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={pageSize} total={data.meta.total} onChange={setPage} />
        </>
      )}
    </div>
  );
}
