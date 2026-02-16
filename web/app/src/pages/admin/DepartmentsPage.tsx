import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import type { Department, PaginatedResponse } from '../../types';

export default function DepartmentsPage() {
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['departments', page],
    queryFn: async () => {
      const { data } = await api.get('/departments', { params: { page, page_size: 20 } });
      return data as PaginatedResponse<Department>;
    },
  });

  const create = useMutation({
    mutationFn: () => api.post('/departments', { name }),
    onSuccess: () => {
      setName('');
      setShowForm(false);
      setError('');
      queryClient.invalidateQueries({ queryKey: ['departments'] });
    },
    onError: (err: unknown) => {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed');
    },
  });

  const deleteDept = useMutation({
    mutationFn: (id: string) => api.delete(`/departments/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['departments'] }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Departments</h2>
        <button onClick={() => setShowForm(!showForm)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          {showForm ? 'Cancel' : 'New Department'}
        </button>
      </div>

      {showForm && (
        <Card className="mb-4">
          <form onSubmit={(e) => { e.preventDefault(); create.mutate(); }} className="flex gap-3 items-end">
            <div className="flex-1">
              {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} required className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <button type="submit" disabled={create.isPending} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">Create</button>
          </form>
        </Card>
      )}

      <Card>
        {isLoading ? <Loading /> : !data?.data.length ? (
          <p className="text-sm text-gray-500">No departments.</p>
        ) : (
          <>
            <Table>
              <thead><tr><Th>Name</Th><Th>Users</Th><Th>Created</Th><Th>Actions</Th></tr></thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((d) => (
                  <tr key={d.id}>
                    <Td>{d.name}</Td>
                    <Td>{d.user_count ?? '-'}</Td>
                    <Td>{new Date(d.created_at).toLocaleDateString()}</Td>
                    <Td>
                      <button onClick={() => deleteDept.mutate(d.id)} className="text-xs text-red-600 hover:underline">Delete</button>
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
