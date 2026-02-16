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

export default function RequestQueuePage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [type, setType] = useState('');
  const [search, setSearch] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['requests', page, status, type, search],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (status) params.status = status;
      if (type) params.type = type;
      if (search) params.search = search;
      const { data } = await api.get('/requests', { params });
      return data as PaginatedResponse<ServiceRequest>;
    },
  });

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-4">{t('page.request_queue.title')}</h2>
      <Card>
        <div className="flex gap-3 mb-4 flex-wrap">
          <input
            placeholder={t('common.search')}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="border rounded-lg px-3 py-1.5 text-sm w-48"
          />
          <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">{t('page.request_queue.all_statuses')}</option>
            <option value="submitted">{t('enum.submitted')}</option>
            <option value="in_review">{t('enum.in_review')}</option>
            <option value="in_progress">{t('enum.in_progress')}</option>
            <option value="resolved">{t('enum.resolved')}</option>
            <option value="rejected">{t('enum.rejected')}</option>
          </select>
          <select value={type} onChange={(e) => { setType(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">{t('page.request_queue.all_types')}</option>
            <option value="incident">{t('enum.incident')}</option>
            <option value="new_equipment">{t('enum.new_equipment')}</option>
            <option value="onboarding">{t('enum.onboarding')}</option>
          </select>
        </div>

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
          <EmptyState message={t('page.request_queue.empty')} />
        ) : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>{t('table.title')}</Th>
                  <Th>{t('table.type')}</Th>
                  <Th>{t('table.priority')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th>{t('table.assigned_to')}</Th>
                  <Th>{t('table.created')}</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <Td><Link to={`/requests/${r.id}`} className="text-blue-600 hover:underline">{r.title}</Link></Td>
                    <Td>{t(`enum.${r.type}`)}</Td>
                    <Td><StatusBadge status={r.priority} /></Td>
                    <Td><StatusBadge status={r.status} /></Td>
                    <Td>{r.assigned_to_email || r.assigned_to || '-'}</Td>
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
