import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Pagination } from '../../components/ui/Pagination';
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

export default function MyMaintenancePage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['my-maintenance', page],
    queryFn: async () => {
      const { data } = await api.get('/my/maintenance', { params: { page, page_size: 20 } });
      return data as PaginatedResponse<MaintenanceRecord>;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.my_maintenance.title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.my_maintenance.subtitle')}</p>
      </div>

      <Card>
        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => { void refetch(); }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.my_maintenance.empty')} />
        ) : (
          <>
            <div className="space-y-2">
              {data.data.map((r) => {
                const statusKey = r.status.toLowerCase();
                return (
                  <Link
                    key={r.id}
                    to={`/maintenance/${r.id}`}
                    className="flex items-center justify-between rounded-lg border border-border px-4 py-3 transition-colors hover:bg-muted/50"
                  >
                    <div>
                      <div className="mb-1 flex items-center gap-2">
                        <Badge variant={statusVariant[statusKey] || 'default'}>{t(`enum.maintenance_status.${statusKey}`)}</Badge>
                        <span className="text-xs text-muted-foreground">{t(`enum.maintenance_priority.${r.priority.toLowerCase()}`)}</span>
                      </div>
                      <p className="text-sm text-foreground">{r.title}</p>
                      <p className="font-mono text-xs text-muted-foreground">{r.asset_id}</p>
                    </div>
                    <div className="text-right text-xs text-muted-foreground">
                      {r.scheduled_at ? formatDateTime(r.scheduled_at) : '—'}
                    </div>
                  </Link>
                );
              })}
            </div>
            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </>
        )}
      </Card>
    </div>
  );
}
