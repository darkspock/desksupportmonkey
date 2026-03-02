import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Pagination } from '../../components/ui/Pagination';
import { formatDate } from '../../lib/date';
import { humanizeToken, useI18n } from '../../lib/i18n';
import type { ServiceRequest, PaginatedResponse } from '../../types';

const STATUS_TABS = ['all', 'in_progress', 'waiting_for_employee', 'in_review', 'submitted', 'resolved', 'rejected'] as const;

export default function MyAssignedRequestsPage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['my-assigned-requests', page, statusFilter],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: 20, assigned_to: 'me' };
      if (statusFilter !== 'all') params.status = statusFilter;
      const { data } = await api.get('/requests', { params });
      return data as PaginatedResponse<ServiceRequest>;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          {t('page.my_assigned_requests.title', undefined, { defaultValue: 'My Requests' })}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {t('page.my_assigned_requests.subtitle', undefined, { defaultValue: 'Requests assigned to you' })}
        </p>
      </div>

      {/* Status tabs */}
      <div className="flex gap-1 flex-wrap">
        {STATUS_TABS.map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1); }}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              statusFilter === s
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-accent'
            }`}
          >
            {s === 'all'
              ? t('common.all', undefined, { defaultValue: 'All' })
              : t(`enum.${s}`, undefined, { defaultValue: humanizeToken(s) })}
          </button>
        ))}
      </div>

      {isLoading ? (
        <Loading />
      ) : isError ? (
        <ErrorState
          message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
          onRetry={() => { void refetch(); }}
        />
      ) : !data?.data.length ? (
        <EmptyState message={t('page.my_assigned_requests.empty', undefined, { defaultValue: 'No requests assigned to you' })} />
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border">
            <Table>
              <thead>
                <tr>
                  <Th>{t('table.title')}</Th>
                  <Th>{t('table.type')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th>{t('table.priority')}</Th>
                  <Th>{t('table.created_at')}</Th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((r) => (
                  <Tr key={r.id}>
                    <Td>
                      <Link to={`/requests/${r.id}`} className="font-medium text-foreground hover:text-primary transition-colors">
                        {r.title}
                      </Link>
                    </Td>
                    <Td><StatusBadge status={r.type} /></Td>
                    <Td><StatusBadge status={r.status} /></Td>
                    <Td><StatusBadge status={r.priority} /></Td>
                    <Td className="text-sm text-muted-foreground">{formatDate(r.created_at)}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          </div>
          <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
        </>
      )}
    </div>
  );
}
