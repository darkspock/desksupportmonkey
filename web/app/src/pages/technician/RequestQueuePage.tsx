import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import type { ServiceRequest, PaginatedResponse } from '../../types';

export default function RequestQueuePage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [type, setType] = useState('');
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
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
      <h2 className="text-xl font-bold text-gray-900 mb-4">Request Queue</h2>
      <Card>
        <div className="flex gap-3 mb-4 flex-wrap">
          <input
            placeholder="Search..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="border rounded-lg px-3 py-1.5 text-sm w-48"
          />
          <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">All statuses</option>
            <option value="submitted">Submitted</option>
            <option value="in_review">In Review</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="rejected">Rejected</option>
          </select>
          <select value={type} onChange={(e) => { setType(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">All types</option>
            <option value="incident">Incident</option>
            <option value="new_equipment">New Equipment</option>
            <option value="onboarding">Onboarding</option>
          </select>
        </div>

        {isLoading ? (
          <Loading />
        ) : !data?.data.length ? (
          <p className="text-sm text-gray-500">No requests found.</p>
        ) : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>Title</Th>
                  <Th>Type</Th>
                  <Th>Priority</Th>
                  <Th>Status</Th>
                  <Th>Assigned To</Th>
                  <Th>Created</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <Td><Link to={`/requests/${r.id}`} className="text-blue-600 hover:underline">{r.title}</Link></Td>
                    <Td>{r.type.replace('_', ' ')}</Td>
                    <Td><StatusBadge status={r.priority} /></Td>
                    <Td><StatusBadge status={r.status} /></Td>
                    <Td>{r.assigned_to || '-'}</Td>
                    <Td>{new Date(r.created_at).toLocaleDateString()}</Td>
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
