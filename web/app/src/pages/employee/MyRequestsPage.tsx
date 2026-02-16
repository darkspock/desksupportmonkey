import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
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
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">{t('page.my_requests.title')}</h2>
        <Link to="/my/requests/new" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          {t('page.my_requests.new')}
        </Link>
      </div>
      <Card>
        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => {
              void refetch();
            }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.my_requests.empty')} />
        ) : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>{t('table.title')}</Th>
                  <Th>{t('table.type')}</Th>
                  <Th>{t('table.priority')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th>{t('table.created')}</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <Td>
                      <Link to={`/requests/${r.id}`} className="text-blue-600 hover:underline">
                        {r.title}
                      </Link>
                    </Td>
                    <Td>{t(`enum.${r.type}`)}</Td>
                    <Td><StatusBadge status={r.priority} /></Td>
                    <Td><StatusBadge status={r.status} /></Td>
                    <Td>{formatDate(r.created_at)}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </>
        )}
      </Card>
    </div>
  );
}
