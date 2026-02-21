import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Tooltip } from '../../components/ui/Tooltip';
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {t('page.maintenance.title')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('page.maintenance.subtitle')}
          </p>
        </div>
        <Link
          to="/maintenance/new"
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 12h14M12 5v14" />
          </svg>
          {t('page.maintenance.new')}
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <svg
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            type="search"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder={t('page.maintenance.search_placeholder')}
            className="w-full pl-9 bg-card"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="w-[150px] bg-card"
          >
            <option value="">{t('page.maintenance.all_statuses')}</option>
            {['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'SKIPPED'].map((s) => (
              <option key={s} value={s}>{t(`enum.maintenance_status.${s.toLowerCase()}`)}</option>
            ))}
          </select>
          <select
            value={priority}
            onChange={(e) => { setPriority(e.target.value); setPage(1); }}
            className="w-[150px] bg-card"
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
        <>
          <Table>
            <thead>
              <tr className="hover:bg-transparent">
                <Th className="pl-4">{t('table.status')}</Th>
                <Th>{t('table.priority')}</Th>
                <Th>{t('table.title')}</Th>
                <Th>{t('table.employee')}</Th>
                <Th>{t('table.asset')}</Th>
                <Th>{t('table.date')}</Th>
                <Th className="pr-4"><span className="sr-only">{t('table.actions')}</span></Th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((r) => {
                const statusKey = r.status.toLowerCase();
                const priorityKey = r.priority.toLowerCase();
                return (
                  <Tr key={r.id}>
                    <Td className="pl-4">
                      <Badge variant={statusVariant[statusKey] || 'default'}>
                        {t(`enum.maintenance_status.${statusKey}`)}
                      </Badge>
                    </Td>
                    <Td>
                      <Badge variant={priorityVariant[priorityKey] || 'default'}>
                        {t(`enum.maintenance_priority.${priorityKey}`)}
                      </Badge>
                    </Td>
                    <Td>{r.title}</Td>
                    <Td>{r.employee_name || r.employee_email || '—'}</Td>
                    <Td><span className="font-mono text-xs">{r.asset_id.slice(0, 8)}</span></Td>
                    <Td>{r.scheduled_at ? formatDateTime(r.scheduled_at) : '—'}</Td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center justify-end">
                        <Tooltip content={t('table.details')}>
                          <Link
                            to={`/maintenance/${r.id}`}
                            aria-label={t('table.details')}
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                          >
                            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                              <circle cx="12" cy="12" r="3" />
                            </svg>
                          </Link>
                        </Tooltip>
                      </div>
                    </td>
                  </Tr>
                );
              })}
            </tbody>
          </Table>
          <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
        </>
      )}
    </div>
  );
}
