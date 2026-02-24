import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { ErrorState } from '../../components/ui/StateBlock';
import { Badge } from '../../components/ui/Badge';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../components/ui/Toast';
import type { AuditEntryDetail, ComplianceControl } from '../../types';

export default function AuditEntryDetailPage() {
  const { t } = useI18n();
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { id } = useParams<{ id: string }>();
  const [showAddTag, setShowAddTag] = useState(false);
  const [selectedControlId, setSelectedControlId] = useState('');

  const { data: entry, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['audit-entry', id],
    queryFn: async () => {
      const { data } = await api.get(`/audit/${id}`);
      return data as AuditEntryDetail;
    },
  });

  const { data: controls } = useQuery({
    queryKey: ['compliance-controls'],
    queryFn: async () => {
      const { data } = await api.get('/audit/controls');
      return data.data as ComplianceControl[];
    },
    enabled: showAddTag,
  });

  const addTagMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/audit/${id}/tags`, { control_ids: [selectedControlId] });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit-entry', id] });
      toast.success(t('audit.tags.added'));
      setShowAddTag(false);
      setSelectedControlId('');
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      toast.error(message);
    },
  });

  const removeTagMutation = useMutation({
    mutationFn: async (tagId: string) => {
      await api.delete(`/audit/${id}/tags/${tagId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit-entry', id] });
      toast.success(t('audit.tags.removed'));
    },
  });

  const formatDate = (iso: string | null) => {
    if (!iso) return '-';
    return new Date(iso).toLocaleString();
  };

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />;
  if (!entry) return null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/audit')}
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4 mr-1" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
          {t('audit.detail.back')}
        </button>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('audit.detail.title')}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1 text-sm font-mono">{entry.id}</p>
      </div>

      {/* Metadata Grid */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('audit.detail.metadata')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Field label={t('audit.detail.timestamp')} value={formatDate(entry.created_at)} />
          <Field label={t('audit.detail.actor_email')} value={entry.actor_email} />
          <Field label={t('audit.detail.actor_id')} value={entry.actor_id || '-'} mono />
          <Field label={t('audit.detail.action')} value={entry.action} />
          <Field label={t('audit.detail.resource_type')} value={entry.resource_type} />
          <Field label={t('audit.detail.resource_id')} value={entry.resource_id || '-'} mono />
          <Field label={t('audit.detail.http_method')}>
            <Badge variant={entry.http_method === 'GET' ? 'info' : entry.http_method === 'POST' ? 'success' : entry.http_method === 'DELETE' ? 'danger' : 'warning'}>
              {entry.http_method}
            </Badge>
          </Field>
          <Field label={t('audit.detail.http_path')} value={entry.http_path} mono />
          <Field label={t('audit.detail.response_status')}>
            <Badge variant={entry.response_status < 400 ? 'success' : entry.response_status < 500 ? 'warning' : 'danger'}>
              {entry.response_status}
            </Badge>
          </Field>
          <Field label={t('audit.detail.ip_address')} value={entry.ip_address || '-'} />
          <Field label={t('audit.detail.user_agent')} value={entry.user_agent || '-'} />
          <Field label={t('audit.detail.hash')} value={entry.hash.slice(0, 24) + '...'} mono />
        </div>
      </div>

      {/* Request Data */}
      {entry.request_data && Object.keys(entry.request_data).length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('audit.detail.request_data')}</h2>
          <pre className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 text-sm text-gray-800 dark:text-gray-200 overflow-auto max-h-64 font-mono">
            {JSON.stringify(entry.request_data, null, 2)}
          </pre>
        </div>
      )}

      {/* Compliance Tags */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{t('audit.tags.title')}</h2>
          <button
            onClick={() => setShowAddTag(true)}
            className="inline-flex items-center rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            {t('audit.tags.add')}
          </button>
        </div>

        {entry.tags.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">{t('audit.tags.none')}</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {entry.tags.map((tag) => (
              <div key={tag.id} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
                <div>
                  <span className="text-xs font-medium text-purple-700 dark:text-purple-300">{tag.framework}</span>
                  <span className="mx-1 text-purple-400">|</span>
                  <span className="text-sm font-medium text-purple-900 dark:text-purple-100">{tag.control_code}</span>
                  <span className="ml-1 text-xs text-purple-600 dark:text-purple-400">{tag.control_name}</span>
                </div>
                <button
                  onClick={() => removeTagMutation.mutate(tag.id)}
                  className="text-purple-400 hover:text-red-500 transition-colors"
                  title={t('audit.tags.remove')}
                >
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Tag Modal */}
      {showAddTag && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 w-96">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('audit.tags.add_title')}</h2>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('audit.tags.select_control')}</label>
              <select
                value={selectedControlId}
                onChange={(e) => setSelectedControlId(e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
              >
                <option value="">{t('common.select')}</option>
                {controls?.filter(c => c.is_active).map((c) => (
                  <option key={c.id} value={c.id}>{c.framework} - {c.code}: {c.name}</option>
                ))}
              </select>
            </div>
            <div className="flex gap-3 justify-end">
              <button onClick={() => { setShowAddTag(false); setSelectedControlId(''); }} className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                {t('common.cancel')}
              </button>
              <button
                onClick={() => addTagMutation.mutate()}
                disabled={!selectedControlId || addTagMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {addTagMutation.isPending ? t('common.working') : t('common.add')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, value, mono, children }: { label: string; value?: string; mono?: boolean; children?: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">{label}</dt>
      <dd className={`mt-1 text-sm text-gray-900 dark:text-white ${mono ? 'font-mono' : ''}`}>
        {children || value || '-'}
      </dd>
    </div>
  );
}
