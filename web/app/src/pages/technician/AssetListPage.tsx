import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import type { Asset, PaginatedResponse } from '../../types';

export default function AssetListPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [type, setType] = useState('');
  const [status, setStatus] = useState('');

  const { data, isLoading } = useQuery({
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
        <h2 className="text-xl font-bold text-gray-900">Asset Inventory</h2>
        <div className="flex gap-2">
          <Link to="/assets/import" className="border px-4 py-2 rounded-lg text-sm hover:bg-gray-50">
            Import CSV
          </Link>
          <Link to="/assets/new" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
            New Asset
          </Link>
        </div>
      </div>
      <Card>
        <div className="flex gap-3 mb-4 flex-wrap">
          <input placeholder="Search..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm w-48" />
          <select value={type} onChange={(e) => { setType(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">All types</option>
            {['laptop', 'desktop', 'phone', 'tablet', 'monitor', 'printer', 'other'].map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">All statuses</option>
            {['in_stock', 'assigned', 'in_repair', 'decommissioned'].map((s) => (
              <option key={s} value={s}>{s.replace('_', ' ')}</option>
            ))}
          </select>
        </div>

        {isLoading ? <Loading /> : !data?.data.length ? (
          <p className="text-sm text-gray-500">No assets found.</p>
        ) : (
          <>
            <Table>
              <thead>
                <tr><Th>Brand</Th><Th>Model</Th><Th>Serial</Th><Th>Type</Th><Th>Status</Th><Th>Assigned</Th></tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((a) => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <Td><Link to={`/assets/${a.id}`} className="text-blue-600 hover:underline">{a.brand}</Link></Td>
                    <Td>{a.model}</Td>
                    <Td>{a.serial_number}</Td>
                    <Td>{a.type}</Td>
                    <Td><StatusBadge status={a.status} /></Td>
                    <Td>{a.assigned_to || '-'}</Td>
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
