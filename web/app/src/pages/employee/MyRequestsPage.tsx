import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { ServiceRequest, PaginatedResponse } from '../../types';

export default function MyRequestsPage() {
  const [page, setPage] = useState(1);
  const { t } = useI18n();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['my-requests', page],
    queryFn: async () => {
      const { data } = await api.get('/my/requests', { params: { page, page_size: 20 } });
      return data as PaginatedResponse<ServiceRequest>;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.my_requests.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.my_requests.subtitle')}</p>
        </div>
        <Link
          to="/my/requests/new"
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 12h14M12 5v14" />
          </svg>
          {t('page.my_requests.new')}
        </Link>
      </div>

      {/* Table */}
      <Card className="overflow-hidden p-0">
        {isLoading ? (
          <div className="p-5"><Loading /></div>
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
              onRetry={() => { void refetch(); }}
            />
          </div>
        ) : !data?.data.length ? (
          <div className="p-5"><EmptyState message={t('page.my_requests.empty')} /></div>
        ) : (
          <>
            <Table>
              <thead>
                <tr className="hover:bg-transparent">
                  <Th className="pl-4">{t('table.title')}</Th>
                  <Th>{t('table.type')}</Th>
                  <Th>{t('table.priority')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th>{t('table.created')}</Th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((r) => (
                  <Tr key={r.id}>
                    <Td className="pl-4">
                      <Link to={`/my/requests/${r.id}`} className="text-primary hover:underline">
                        {r.title}
                      </Link>
                    </Td>
                    <Td>
                      <span>{t(`enum.${r.type}`)}</span>
                      {r.subtype && <span className="ml-1 text-xs text-muted-foreground">({t(`enum.${r.subtype}`)})</span>}
                    </Td>
                    <Td><StatusBadge status={r.priority} /></Td>
                    <Td><StatusBadge status={r.status} /></Td>
                    <Td>{formatDate(r.created_at)}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
            <div className="p-4">
              <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
