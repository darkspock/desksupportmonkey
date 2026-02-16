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
import { useI18n } from '../../lib/i18n';
import type { Asset, PaginatedResponse } from '../../types';

export default function AssetListPage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [type, setType] = useState('');
  const [status, setStatus] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['assets', page, search, type, status],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (search) params.search = search;
      if (type) params.type = type;
      if (status) params.status = status;
      const { data } = await api.get('/assets', { params });
      return data as PaginatedResponse<Asset>;
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">{t('page.asset_list.title')}</h2>
        <div className="flex gap-2">
          <Link to="/assets/import" className="border px-4 py-2 rounded-lg text-sm hover:bg-gray-50">
            {t('page.asset_list.import_csv')}
          </Link>
          <Link to="/assets/new" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
            {t('page.asset_list.new_asset')}
          </Link>
        </div>
      </div>
      <Card>
        <div className="flex gap-3 mb-4 flex-wrap">
          <input placeholder={t('common.search')} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm w-48" />
          <select value={type} onChange={(e) => { setType(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">{t('page.asset_list.all_types')}</option>
            {['laptop', 'desktop', 'phone', 'tablet', 'monitor', 'printer', 'other'].map((assetType) => (
              <option key={assetType} value={assetType}>{t(`enum.${assetType}`)}</option>
            ))}
          </select>
          <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">{t('page.asset_list.all_statuses')}</option>
            {['in_stock', 'assigned', 'in_repair', 'decommissioned'].map((s) => (
              <option key={s} value={s}>{t(`enum.${s}`)}</option>
            ))}
          </select>
        </div>

        {isLoading ? <Loading /> : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => {
              void refetch();
            }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.asset_list.empty')} />
        ) : (
          <>
            <Table>
              <thead>
                <tr><Th>{t('table.brand')}</Th><Th>{t('table.model')}</Th><Th>{t('table.serial')}</Th><Th>{t('table.type')}</Th><Th>{t('table.status')}</Th><Th>{t('table.assigned')}</Th></tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((a) => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <Td><Link to={`/assets/${a.id}`} className="text-blue-600 hover:underline">{a.brand}</Link></Td>
                    <Td>{a.model}</Td>
                    <Td>{a.serial_number}</Td>
                    <Td>{t(`enum.${a.type}`)}</Td>
                    <Td><StatusBadge status={a.status} /></Td>
                    <Td>{a.assigned_to_email || a.assigned_to || '-'}</Td>
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
