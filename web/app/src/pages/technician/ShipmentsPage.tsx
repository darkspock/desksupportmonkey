import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Badge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
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

const directionColors: Record<string, string> = {
  outbound: 'info',
  inbound: 'warning',
};

export default function ShipmentsPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [directionFilter, setDirectionFilter] = useState('');
  const [destFilter, setDestFilter] = useState('');
  const navigate = useNavigate();
  const { t } = useI18n();

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

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.shipments.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.shipments.subtitle')}</p>
        </div>
        <Link
          to="/shipments/new"
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 12h14M12 5v14" />
          </svg>
          {t('page.shipments.new')}
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="w-[150px] bg-card"
        >
          <option value="">{t('page.shipments.all_statuses')}</option>
          {['draft', 'dispatched', 'in_transit', 'delivered', 'failed', 'cancelled'].map((s) => (
            <option key={s} value={s}>{t(`enum.shipment_status.${s}`)}</option>
          ))}
        </select>
        <select
          value={directionFilter}
          onChange={(e) => { setDirectionFilter(e.target.value); setPage(1); }}
          className="w-[150px] bg-card"
        >
          <option value="">{t('page.shipments.all_directions')}</option>
          {['outbound', 'inbound'].map((d) => (
            <option key={d} value={d}>{t(`enum.shipment_direction.${d}`)}</option>
          ))}
        </select>
        <select
          value={destFilter}
          onChange={(e) => { setDestFilter(e.target.value); setPage(1); }}
          className="w-[150px] bg-card"
        >
          <option value="">{t('page.shipments.all_destinations')}</option>
          {['employee_home', 'office', 'vendor'].map((d) => (
            <option key={d} value={d}>{t(`enum.destination_type.${d}`)}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      {isLoading ? <Loading /> : isError ? (
        <ErrorState
          message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
          onRetry={() => { void refetch(); }}
        />
      ) : !data?.data.length ? (
        <EmptyState message={t('page.shipments.empty')} />
      ) : (
        <>
          <Table>
            <thead>
              <tr className="hover:bg-transparent">
                <Th className="pl-4">{t('table.status')}</Th>
                <Th>{t('table.direction')}</Th>
                <Th>{t('table.destination')}</Th>
                <Th>{t('table.carrier')}</Th>
                <Th>{t('table.tracking')}</Th>
                <Th>{t('table.recipient')}</Th>
                <Th>{t('table.items')}</Th>
                <Th>{t('table.dispatched')}</Th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((s) => (
                <Tr
                  key={s.id}
                  className="cursor-pointer"
                  onClick={() => navigate(`/shipments/${s.id}`)}
                >
                  <Td className="pl-4">
                    <Badge variant={statusColors[s.status] || 'default'}>
                      {t(`enum.shipment_status.${s.status}`)}
                    </Badge>
                  </Td>
                  <Td>
                    <Badge variant={directionColors[s.direction] || 'default'}>
                      {t(`enum.shipment_direction.${s.direction}`)}
                    </Badge>
                  </Td>
                  <Td>{t(`enum.destination_type.${s.destination_type}`)}</Td>
                  <Td>{s.carrier || '—'}</Td>
                  <Td>{s.tracking_number || '—'}</Td>
                  <Td>{s.recipient_name || '—'}</Td>
                  <Td>{s.item_count}</Td>
                  <Td>{s.dispatched_at ? formatDateTime(s.dispatched_at) : '—'}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
          <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
        </>
      )}
    </div>
  );
}
