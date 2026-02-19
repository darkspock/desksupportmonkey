import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { Shipment, PaginatedResponse } from '../../types';

const statusColors: Record<string, string> = {
  draft: 'default',
  dispatched: 'info',
  in_transit: 'warning',
  delivered: 'success',
  failed: 'danger',
  cancelled: 'default',
};

export default function MyShipmentsPage() {
  const [page, setPage] = useState(1);
  const { t } = useI18n();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['my-shipments', page],
    queryFn: async () => {
      const { data } = await api.get('/my/shipments', { params: { page, page_size: 20 } });
      return data as PaginatedResponse<Shipment>;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.my_shipments.title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.my_shipments.subtitle')}</p>
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
          <EmptyState message={t('page.my_shipments.empty')} />
        ) : (
          <>
            <div className="space-y-2">
              {data.data.map((s) => (
                <div key={s.id} className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
                  <div className="flex items-center gap-4">
                    <Badge variant={statusColors[s.status] || 'default'}>
                      {t(`enum.shipment_status.${s.status}`)}
                    </Badge>
                    <div>
                      <p className="text-sm text-foreground">{s.carrier || '—'}</p>
                      {s.tracking_url ? (
                        <a href={s.tracking_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">
                          {s.tracking_number || t('page.shipment_detail.tracking')}
                        </a>
                      ) : s.tracking_number ? (
                        <p className="text-xs text-muted-foreground">{s.tracking_number}</p>
                      ) : null}
                    </div>
                    <span className="text-xs text-muted-foreground">{s.item_count} {t('table.items').toLowerCase()}</span>
                  </div>
                  <div className="text-right text-xs text-muted-foreground">
                    {s.dispatched_at && <p>{t('table.dispatched')}: {formatDateTime(s.dispatched_at)}</p>}
                    {s.delivered_at && <p>{t('table.delivered')}: {formatDateTime(s.delivered_at)}</p>}
                  </div>
                </div>
              ))}
            </div>
            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </>
        )}
      </Card>
    </div>
  );
}
