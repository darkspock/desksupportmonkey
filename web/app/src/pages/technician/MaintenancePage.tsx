import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Pagination } from '../../components/ui/Pagination';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { MaintenanceRecord, PaginatedResponse } from '../../types';

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  scheduled: 'info',
  in_progress: 'warning',
  completed: 'success',
  cancelled: 'default',
  skipped: 'default',
};

const priorityVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  low: 'default',
  medium: 'info',
  high: 'warning',
  critical: 'danger',
};

export default function MaintenancePage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [search, setSearch] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['maintenance', page, status, priority, search],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: 20 };
      if (status) params.status = status;
      if (priority) params.priority = priority;
      if (search.trim()) params.search = search.trim();
      const { data } = await api.get('/maintenance', { params });
      return data as PaginatedResponse<MaintenanceRecord>;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.maintenance.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.maintenance.subtitle')}</p>
        </div>
        <Link
          to="/maintenance/new"
          className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.maintenance.new')}
        </Link>
      </div>

      <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <input
            type="search"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder={t('page.maintenance.search_placeholder')}
            className="w-full sm:col-span-1"
          />
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="w-full"
          >
            <option value="">{t('page.maintenance.all_statuses')}</option>
            {['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'SKIPPED'].map((s) => (
              <option key={s} value={s}>{t(`enum.maintenance_status.${s.toLowerCase()}`)}</option>
            ))}
          </select>
          <select
            value={priority}
            onChange={(e) => { setPriority(e.target.value); setPage(1); }}
            className="w-full"
          >
            <option value="">{t('page.maintenance.all_priorities')}</option>
            {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((p) => (
              <option key={p} value={p}>{t(`enum.maintenance_priority.${p.toLowerCase()}`)}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? <Loading /> : isError ? (
        <ErrorState
          message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
          onRetry={() => { void refetch(); }}
        />
      ) : !data?.data.length ? (
        <EmptyState message={t('page.maintenance.empty')} />
      ) : (
        <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/40">
                <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.status')}</th>
                <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.priority')}</th>
                <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.title')}</th>
                <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.employee')}</th>
                <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.asset')}</th>
                <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.date')}</th>
                <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((r) => {
                const statusKey = r.status.toLowerCase();
                const priorityKey = r.priority.toLowerCase();
                return (
                  <tr key={r.id} className="border-b border-border/80 hover:bg-accent/30">
                    <td className="px-4 py-3 align-top">
                      <Badge variant={statusVariant[statusKey] || 'default'}>
                        {t(`enum.maintenance_status.${statusKey}`)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 align-top">
                      <Badge variant={priorityVariant[priorityKey] || 'default'}>
                        {t(`enum.maintenance_priority.${priorityKey}`)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 align-top text-foreground">{r.title}</td>
                    <td className="px-4 py-3 align-top text-foreground">{r.employee_name || r.employee_email || '—'}</td>
                    <td className="px-4 py-3 align-top">
                      <span className="font-mono text-xs text-muted-foreground">{r.asset_id.slice(0, 8)}</span>
                    </td>
                    <td className="px-4 py-3 align-top text-muted-foreground">{r.scheduled_at ? formatDateTime(r.scheduled_at) : '—'}</td>
                    <td className="px-4 py-3 align-top">
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/maintenance/${r.id}`}
                          className="inline-flex h-8 items-center rounded-md border border-border px-3 text-xs font-medium text-foreground hover:bg-accent"
                        >
                          {t('table.details')}
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
            </table>
          </div>
          <div className="border-t border-border bg-card px-4 py-3">
            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </div>
        </div>
      )}
    </div>
  );
}
