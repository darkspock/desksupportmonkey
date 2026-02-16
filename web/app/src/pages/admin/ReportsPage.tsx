import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { Report, PaginatedResponse } from '../../types';

export default function ReportsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [reportType, setReportType] = useState('asset_inventory');
  const { showToast } = useToast();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      const { data } = await api.get('/reports', { params: { page_size: 50 } });
      return data as PaginatedResponse<Report>;
    },
    refetchInterval: 5000,
  });

  const create = useMutation({
    mutationFn: () => api.post('/reports', { type: reportType }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      showToast({ title: t('page.reports.toast_requested'), variant: 'success' });
    },
    onError: () => {
      showToast({ title: t('page.reports.error_request'), variant: 'error' });
    },
  });

  const download = async (id: string) => {
    try {
      const { data } = await api.get(`/reports/${id}/download`);
      window.open(data.data.download_url, '_blank');
    } catch {
      showToast({ title: t('page.reports.error_download_not_ready'), variant: 'error' });
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-4">{t('page.reports.title')}</h2>

      <Card className="mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('page.reports.generate_new')}</h3>
        <div className="flex gap-3 items-end">
          <div>
            <label className="block text-sm text-gray-600 mb-1">{t('table.type')}</label>
            <select value={reportType} onChange={(e) => setReportType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
              <option value="asset_inventory">{t('enum.asset_inventory')}</option>
              <option value="request_summary">{t('enum.request_summary')}</option>
              <option value="technician_performance">{t('enum.technician_performance')}</option>
            </select>
          </div>
          <button onClick={() => create.mutate()} disabled={create.isPending} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {create.isPending ? t('page.reports.requesting') : t('page.reports.generate')}
          </button>
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('page.reports.history')}</h3>
        {isLoading ? <Loading /> : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => {
              void refetch();
            }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.reports.empty')} />
        ) : (
          <Table>
            <thead><tr><Th>{t('table.type')}</Th><Th>{t('table.status')}</Th><Th>{t('table.requested')}</Th><Th>{t('table.completed')}</Th><Th>{t('table.actions')}</Th></tr></thead>
            <tbody className="divide-y divide-gray-100">
              {data.data.map((r) => (
                <tr key={r.id}>
                  <Td>{t(`enum.${r.type}`)}</Td>
                  <Td><StatusBadge status={r.status} /></Td>
                  <Td>{formatDateTime(r.created_at)}</Td>
                  <Td>{formatDateTime(r.completed_at)}</Td>
                  <Td>
                    {r.status === 'completed' && (
                      <button onClick={() => download(r.id)} className="text-xs text-blue-600 hover:underline">{t('page.reports.download')}</button>
                    )}
                    {r.status === 'failed' && (
                      <span className="text-xs text-red-500">{r.error_message || t('enum.failed')}</span>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
