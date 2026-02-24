import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Loading } from '../../components/ui/Loading';
import { Pagination } from '../../components/ui/Pagination';
import { formatDateTime } from '../../lib/date';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { AssetLocation, PaginatedResponse, Shipment } from '../../types';

const statusColors: Record<string, string> = {
  DRAFT: 'default',
  DISPATCHED: 'info',
  IN_TRANSIT: 'warning',
  DELIVERED: 'success',
  FAILED: 'danger',
  CANCELLED: 'default',
};

function StatCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-border bg-card px-5 py-4 shadow-sm">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-foreground">{value}</p>
    </div>
  );
}

export default function ShipmentsPage() {
  const { t } = useI18n();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['shipments', page],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: 20 };
      const { data } = await api.get('/shipments', { params });
      return data as PaginatedResponse<Shipment>;
    },
  });

  const statsQuery = useQuery({
    queryKey: ['shipments-stats'],
    queryFn: async () => {
      const { data } = await api.get('/shipments', { params: { page: 1, page_size: 200 } });
      return data as PaginatedResponse<Shipment>;
    },
    staleTime: 30_000,
  });

  const locationsQuery = useQuery({
    queryKey: ['locations-all-for-shipments'],
    queryFn: async () => {
      const { data } = await api.get('/assets/locations', { params: { page_size: 300 } });
      return data as PaginatedResponse<AssetLocation>;
    },
  });

  const rows = useMemo(() => data?.data ?? [], [data?.data]);
  const statsRows = useMemo(() => statsQuery.data?.data ?? [], [statsQuery.data?.data]);
  const locationMap = useMemo(
    () => new Map((locationsQuery.data?.data ?? []).map((loc) => [loc.id, loc])),
    [locationsQuery.data?.data],
  );

  const stats = useMemo(() => ({
    total: statsQuery.data?.meta?.total ?? 0,
    inTransit: statsRows.filter((s) => s.status === 'in_transit').length,
    delivered: statsRows.filter((s) => s.status === 'delivered').length,
    pending: statsRows.filter((s) => s.status === 'draft' || s.status === 'dispatched').length,
  }), [statsRows, statsQuery.data?.meta?.total]);

  const refreshShipments = () => {
    queryClient.invalidateQueries({ queryKey: ['shipments'] });
    queryClient.invalidateQueries({ queryKey: ['shipments-stats'] });
  };

  const dispatch = useMutation({
    mutationFn: (shipmentId: string) => api.post(`/shipments/${shipmentId}/dispatch`, {}),
    onSuccess: () => {
      refreshShipments();
      showToast({ title: t('page.shipment_detail.toast_dispatched'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.shipment_detail.error_deliver');
      showToast({ title: detail, variant: 'error' });
    },
  });

  const deliver = useMutation({
    mutationFn: (shipmentId: string) => api.post(`/shipments/${shipmentId}/deliver`, {}),
    onSuccess: () => {
      refreshShipments();
      showToast({ title: t('page.shipment_detail.toast_delivered'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.shipment_detail.error_deliver');
      showToast({ title: detail, variant: 'error' });
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.shipments.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.shipments.subtitle')}</p>
        </div>
        <Link
          to="/shipments/new"
          className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.shipments.new')}
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label={t('page.shipments.stat_total')} value={stats.total} />
        <StatCard label={t('page.shipments.stat_in_transit')} value={stats.inTransit} />
        <StatCard label={t('page.shipments.stat_delivered')} value={stats.delivered} />
        <StatCard label={t('page.shipments.stat_pending')} value={stats.pending} />
      </div>

      {isLoading ? (
        <Loading />
      ) : isError ? (
        <ErrorState
          message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
          onRetry={() => { void refetch(); }}
        />
      ) : !rows.length ? (
        <EmptyState message={t('page.shipments.empty')} />
      ) : (
        <>
          <Table className="min-w-[980px]">
            <thead>
              <tr className="hover:bg-transparent">
                <Th>{t('page.shipments.col_id')}</Th>
                <Th>{t('page.shipments.col_route')}</Th>
                <Th>{t('page.shipments.col_carrier_info')}</Th>
                <Th>{t('table.status')}</Th>
                <Th>{t('table.date')}</Th>
                <Th>{t('table.actions')}</Th>
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => {
                const origin = s.origin_location_id ? locationMap.get(s.origin_location_id) : undefined;
                const destination = s.destination_location_id ? locationMap.get(s.destination_location_id) : undefined;
                return (
                  <Tr key={s.id}>
                    <Td>
                      <p className="font-medium text-foreground">{s.id.slice(0, 8)}</p>
                      <p className="text-xs text-muted-foreground">{t(`enum.shipment_direction.${s.direction}`)}</p>
                    </Td>
                    <Td>
                      <p className="text-foreground">{origin?.name || '—'}</p>
                      <p className="text-xs text-muted-foreground">
                        {destination?.name || s.recipient_name || t('common.na')}
                      </p>
                    </Td>
                    <Td>
                      <p className="text-foreground">{s.carrier || '—'}</p>
                      <p className="font-mono text-xs text-muted-foreground">{s.tracking_number || '—'}</p>
                    </Td>
                    <Td>
                      <Badge variant={statusColors[s.status] || 'default'}>
                        {t(`enum.shipment_status.${s.status}`)}
                      </Badge>
                    </Td>
                    <Td className="text-muted-foreground">
                      {formatDateTime(s.created_at || s.dispatched_at)}
                    </Td>
                    <Td>
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          to={`/shipments/${s.id}`}
                          className="inline-flex h-8 items-center rounded-md border border-border px-3 text-xs font-medium text-foreground hover:bg-accent"
                        >
                          {t('table.details')}
                        </Link>
                        {s.status.toUpperCase() === 'DRAFT' && (
                          <button
                            type="button"
                            onClick={() => dispatch.mutate(s.id)}
                            disabled={dispatch.isPending}
                            className="inline-flex h-8 items-center rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
                          >
                            {t('page.shipment_detail.dispatch')}
                          </button>
                        )}
                        {(s.status.toUpperCase() === 'DISPATCHED' || s.status.toUpperCase() === 'IN_TRANSIT') && (
                          <button
                            type="button"
                            onClick={() => deliver.mutate(s.id)}
                            disabled={deliver.isPending}
                            className="inline-flex h-8 items-center rounded-md bg-success px-3 text-xs font-medium text-white shadow-xs hover:bg-success/90 disabled:opacity-50"
                          >
                            {t('page.shipment_detail.deliver')}
                          </button>
                        )}
                        {s.tracking_url && (
                          <a
                            href={s.tracking_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex h-8 items-center rounded-md border border-border px-3 text-xs font-medium text-foreground hover:bg-accent"
                          >
                            {t('page.shipments.track')}
                          </a>
                        )}
                      </div>
                    </Td>
                  </Tr>
                );
              })}
            </tbody>
          </Table>
          <div className="flex items-center justify-between pt-2">
            <span className="text-sm text-muted-foreground">{t('common.total', { count: String(data?.meta.total ?? 0) })}</span>
            <Pagination page={page} pageSize={20} total={data?.meta.total ?? 0} onChange={setPage} />
          </div>
        </>
      )}
    </div>
  );
}
