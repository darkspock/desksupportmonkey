import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Loading } from '../../components/ui/Loading';
import { Pagination } from '../../components/ui/Pagination';
import { formatDateTime } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { PaginatedResponse, Shipment, ShippingAddress } from '../../types';

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
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [directionFilter, setDirectionFilter] = useState('');
  const [destFilter, setDestFilter] = useState('');
  const [carrierFilter, setCarrierFilter] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['shipments', page, statusFilter, directionFilter, destFilter],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: 20 };
      if (statusFilter) params.status = statusFilter;
      if (directionFilter) params.direction = directionFilter;
      if (destFilter) params.destination_type = destFilter;
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

  const addressesQuery = useQuery({
    queryKey: ['addresses-all-for-shipments'],
    queryFn: async () => {
      const { data } = await api.get('/addresses', { params: { page_size: 300, is_active: true } });
      return data as PaginatedResponse<ShippingAddress>;
    },
  });

  const rows = useMemo(() => data?.data ?? [], [data?.data]);
  const statsRows = useMemo(() => statsQuery.data?.data ?? [], [statsQuery.data?.data]);
  const addressMap = useMemo(
    () => new Map((addressesQuery.data?.data ?? []).map((a) => [a.id, a])),
    [addressesQuery.data?.data],
  );

  const carriers = useMemo(
    () => Array.from(new Set(rows.map((s) => s.carrier).filter((c): c is string => Boolean(c)))).sort(),
    [rows],
  );

  const filteredRows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return rows.filter((s) => {
      if (carrierFilter && (s.carrier ?? '') !== carrierFilter) return false;

      if (!q) return true;
      const origin = s.origin_address_id ? addressMap.get(s.origin_address_id)?.label ?? '' : '';
      const destination = s.destination_address_id ? addressMap.get(s.destination_address_id)?.label ?? '' : '';
      const haystack = [
        s.id,
        s.tracking_number ?? '',
        s.carrier ?? '',
        s.recipient_name ?? '',
        origin,
        destination,
      ].join(' ').toLowerCase();
      return haystack.includes(q);
    });
  }, [rows, search, carrierFilter, addressMap]);

  const stats = useMemo(() => ({
    total: statsQuery.data?.meta?.total ?? 0,
    inTransit: statsRows.filter((s) => s.status === 'IN_TRANSIT').length,
    delivered: statsRows.filter((s) => s.status === 'DELIVERED').length,
    pending: statsRows.filter((s) => s.status === 'DRAFT' || s.status === 'DISPATCHED').length,
  }), [statsRows, statsQuery.data?.meta?.total]);

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

      <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('page.shipments.search_placeholder')}
            className="w-full sm:col-span-2 lg:col-span-1"
          />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="w-full"
          >
            <option value="">{t('page.shipments.all_statuses')}</option>
            {['DRAFT', 'DISPATCHED', 'IN_TRANSIT', 'DELIVERED', 'FAILED', 'CANCELLED'].map((s) => (
              <option key={s} value={s}>{t(`enum.shipment_status.${s}`)}</option>
            ))}
          </select>

          <select
            value={directionFilter}
            onChange={(e) => { setDirectionFilter(e.target.value); setPage(1); }}
            className="w-full"
          >
            <option value="">{t('page.shipments.all_directions')}</option>
            {['OUTBOUND', 'INBOUND'].map((d) => (
              <option key={d} value={d}>{t(`enum.shipment_direction.${d}`)}</option>
            ))}
          </select>

          <select
            value={destFilter}
            onChange={(e) => { setDestFilter(e.target.value); setPage(1); }}
            className="w-full"
          >
            <option value="">{t('page.shipments.all_destinations')}</option>
            {['EMPLOYEE_HOME', 'OFFICE', 'VENDOR'].map((d) => (
              <option key={d} value={d}>{t(`enum.destination_type.${d}`)}</option>
            ))}
          </select>

          <select
            value={carrierFilter}
            onChange={(e) => setCarrierFilter(e.target.value)}
            className="w-full"
          >
            <option value="">{t('page.shipments.all_carriers')}</option>
            {carriers.map((carrier) => (
              <option key={carrier} value={carrier}>{carrier}</option>
            ))}
          </select>
        </div>
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
      ) : filteredRows.length === 0 ? (
        <EmptyState message={t('page.shipments.empty_filtered')} />
      ) : (
        <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/40">
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('page.shipments.col_id')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('page.shipments.col_route')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('page.shipments.col_carrier_info')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.status')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.date')}</th>
                  <th className="px-4 py-2 text-left font-medium text-foreground">{t('table.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((s) => {
                  const origin = s.origin_address_id ? addressMap.get(s.origin_address_id) : undefined;
                  const destination = s.destination_address_id ? addressMap.get(s.destination_address_id) : undefined;
                  return (
                    <tr key={s.id} className="border-b border-border/80 hover:bg-accent/30">
                      <td className="px-4 py-3 align-top">
                        <p className="font-medium text-foreground">{s.id.slice(0, 8)}</p>
                        <p className="text-xs text-muted-foreground">{t(`enum.shipment_direction.${s.direction}`)}</p>
                      </td>
                      <td className="px-4 py-3 align-top">
                        <p className="text-foreground">{origin?.label || '—'}</p>
                        <p className="text-xs text-muted-foreground">
                          {destination?.label || s.recipient_name || t('common.na')}
                        </p>
                      </td>
                      <td className="px-4 py-3 align-top">
                        <p className="text-foreground">{s.carrier || '—'}</p>
                        <p className="font-mono text-xs text-muted-foreground">{s.tracking_number || '—'}</p>
                      </td>
                      <td className="px-4 py-3 align-top">
                        <Badge variant={statusColors[s.status] || 'default'}>
                          {t(`enum.shipment_status.${s.status}`)}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 align-top text-muted-foreground">
                        {formatDateTime(s.created_at || s.dispatched_at)}
                      </td>
                      <td className="px-4 py-3 align-top">
                        <div className="flex flex-wrap items-center gap-2">
                          <Link
                            to={`/shipments/${s.id}`}
                            className="inline-flex h-8 items-center rounded-md border border-border px-3 text-xs font-medium text-foreground hover:bg-accent"
                          >
                            {t('table.details')}
                          </Link>
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
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="border-t border-border bg-card px-4 py-3">
            <Pagination page={page} pageSize={20} total={data?.meta.total ?? 0} onChange={setPage} />
          </div>
        </div>
      )}
    </div>
  );
}
