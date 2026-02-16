import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge, Badge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import type { User, PaginatedResponse } from '../../types';

export default function UsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['users', page, search, roleFilter],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;
      const { data } = await api.get('/users', { params });
      return data as PaginatedResponse<User>;
    },
  });

  const [roleError, setRoleError] = useState('');

  const changeRole = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      api.patch(`/users/${userId}/role`, { role }),
    onSuccess: () => {
      setRoleError('');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to change role';
      setRoleError(msg);
    },
  });

  const toggleActive = useMutation({
    mutationFn: ({ userId, active }: { userId: string; active: boolean }) =>
      api.patch(`/users/${userId}/${active ? 'activate' : 'deactivate'}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-4">Users</h2>
      <Card>
        <div className="flex gap-3 mb-4">
          <input placeholder="Search..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm w-48" />
          <select value={roleFilter} onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">All roles</option>
            {['employee', 'technician', 'admin'].map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>

        {roleError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {roleError}
          </div>
        )}

        {isLoading ? <Loading /> : !data?.data.length ? (
          <p className="text-sm text-gray-500">No users found.</p>
        ) : (
          <>
            <Table>
              <thead><tr><Th>Email</Th><Th>Role</Th><Th>Status</Th><Th>Actions</Th></tr></thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((u) => (
                  <tr key={u.id}>
                    <Td>{u.email}</Td>
                    <Td>
                      <select
                        value={u.role}
                        onChange={(e) => changeRole.mutate({ userId: u.id, role: e.target.value })}
                        className="border rounded px-2 py-1 text-xs"
                      >
                        {['employee', 'technician', 'admin'].map((r) => <option key={r} value={r}>{r}</option>)}
                      </select>
                    </Td>
                    <Td>{u.is_active ? <Badge variant="success">Active</Badge> : <Badge variant="danger">Inactive</Badge>}</Td>
                    <Td>
                      <button
                        onClick={() => toggleActive.mutate({ userId: u.id, active: !u.is_active })}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </Td>
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
