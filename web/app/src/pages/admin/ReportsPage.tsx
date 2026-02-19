import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Tooltip } from '../../components/ui/Tooltip';
import { useToast } from '../../hooks/useToast';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { Report, PaginatedResponse } from '../../types';

export default function ReportsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [reportType, setReportType] = useState('asset_inventory');
  const [generateModalOpen, setGenerateModalOpen] = useState(false);
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
      setGenerateModalOpen(false);
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
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.reports.title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.reports.subtitle')}</p>
      </div>
      <div>
        <button
          type="button"
          onClick={() => setGenerateModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {t('page.reports.generate_new')}
        </button>
      </div>

      <Card>
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
          <Table className="min-w-[920px]">
            <thead>
              <tr>
                <Th>{t('table.type')}</Th>
                <Th>{t('table.status')}</Th>
                <Th>{t('table.requested')}</Th>
                <Th>{t('table.completed')}</Th>
                <Th className="text-right">{t('table.actions')}</Th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((r) => (
                <tr key={r.id}>
                  <Td>{t(`enum.${r.type}`)}</Td>
                  <Td><StatusBadge status={r.status} /></Td>
                  <Td className="whitespace-nowrap">{formatDateTime(r.created_at)}</Td>
                  <Td className="whitespace-nowrap">{r.completed_at ? formatDateTime(r.completed_at) : '-'}</Td>
                  <Td className="text-right">
                    {r.status === 'completed' && (
                      <button
                        type="button"
                        onClick={() => download(r.id)}
                        className="inline-flex h-8 items-center justify-center rounded-md px-2 text-sm font-medium text-primary hover:underline"
                      >
                        {t('page.reports.download')}
                      </button>
                    )}
                    {r.status === 'pending' && (
                      <span className="text-xs text-muted-foreground">-</span>
                    )}
                    {r.status !== 'completed' && r.status !== 'pending' && r.status !== 'failed' && (
                      <span className="text-xs text-muted-foreground">-</span>
                    )}
                    {r.status === 'failed' && (
                      <Tooltip content={r.error_message || t('enum.failed')}>
                        <button
                          type="button"
                          className="inline-flex h-8 items-center justify-center rounded-md px-2 text-xs font-medium text-destructive hover:bg-destructive/10"
                        >
                          {t('enum.failed')}
                        </button>
                      </Tooltip>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      {generateModalOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (!create.isPending) setGenerateModalOpen(false);
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.reports.generate_new')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                create.mutate();
              }}
              className="mt-4 space-y-4"
            >
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('table.type')}</label>
                <select value={reportType} onChange={(e) => setReportType(e.target.value)} className="w-full bg-card">
                  <option value="asset_inventory">{t('enum.asset_inventory')}</option>
                  <option value="request_summary">{t('enum.request_summary')}</option>
                  <option value="technician_performance">{t('enum.technician_performance')}</option>
                  <option value="department_spending">{t('enum.department_spending')}</option>
                </select>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (!create.isPending) setGenerateModalOpen(false);
                  }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={create.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {create.isPending ? t('page.reports.requesting') : t('page.reports.generate')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
