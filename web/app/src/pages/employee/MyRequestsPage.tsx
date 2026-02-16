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

export default function MyRequestsPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['my-requests', page],
    queryFn: async () => {
      const { data } = await api.get('/my/requests', { params: { page, page_size: 20 } });
      return data as PaginatedResponse<ServiceRequest>;
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">My Requests</h2>
        <Link to="/my/requests/new" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          New Request
        </Link>
      </div>
      <Card>
        {isLoading ? (
          <Loading />
        ) : !data?.data.length ? (
          <p className="text-sm text-gray-500">No requests yet.</p>
        ) : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>Title</Th>
                  <Th>Type</Th>
                  <Th>Priority</Th>
                  <Th>Status</Th>
                  <Th>Created</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => window.location.href = `/requests/${r.id}`}>
                    <Td>{r.title}</Td>
                    <Td>{r.type.replace('_', ' ')}</Td>
                    <Td><StatusBadge status={r.priority} /></Td>
                    <Td><StatusBadge status={r.status} /></Td>
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
