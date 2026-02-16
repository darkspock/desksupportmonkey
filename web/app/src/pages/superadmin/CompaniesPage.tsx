import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { StatusBadge } from '../../components/ui/Badge';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import type { Company, PaginatedResponse } from '../../types';

export default function CompaniesPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', admin_email: '', email_domains: '' });
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['companies', page, search],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (search) params.search = search;
      const { data } = await api.get('/companies', { params });
      return data as PaginatedResponse<Company>;
    },
  });

  const create = useMutation({
    mutationFn: () => api.post('/companies', {
      name: form.name,
      admin_email: form.admin_email,
      email_domains: form.email_domains.split(',').map((d) => d.trim()).filter(Boolean),
    }),
    onSuccess: () => {
      setForm({ name: '', admin_email: '', email_domains: '' });
      setShowForm(false);
      setError('');
      queryClient.invalidateQueries({ queryKey: ['companies'] });
    },
    onError: (err: unknown) => {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed');
    },
  });

  const changeStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patch(`/companies/${id}/status`, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['companies'] }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Companies</h2>
        <button onClick={() => setShowForm(!showForm)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          {showForm ? 'Cancel' : 'New Company'}
        </button>
      </div>

      {showForm && (
        <Card className="mb-4">
          <form onSubmit={(e) => { e.preventDefault(); create.mutate(); }} className="space-y-3">
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Admin Email</label>
              <input type="email" value={form.admin_email} onChange={(e) => setForm({ ...form, admin_email: e.target.value })} required className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email Domains (comma-separated)</label>
              <input value={form.email_domains} onChange={(e) => setForm({ ...form, email_domains: e.target.value })} placeholder="company.com, corp.com" className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <button type="submit" disabled={create.isPending} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">
              {create.isPending ? 'Creating...' : 'Create Company'}
            </button>
          </form>
        </Card>
      )}

      <Card>
        <div className="mb-4">
          <input placeholder="Search..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="border rounded-lg px-3 py-1.5 text-sm w-48" />
        </div>

        {isLoading ? <Loading /> : !data?.data.length ? (
          <p className="text-sm text-gray-500">No companies found.</p>
        ) : (
          <>
            <Table>
              <thead><tr><Th>Name</Th><Th>Status</Th><Th>Users</Th><Th>Departments</Th><Th>Actions</Th></tr></thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((c) => (
                  <tr key={c.id}>
                    <Td>{c.name}</Td>
                    <Td><StatusBadge status={c.status} /></Td>
                    <Td>{c.user_count ?? '-'}</Td>
                    <Td>{c.department_count ?? '-'}</Td>
                    <Td>
                      <select
                        value={c.status}
                        onChange={(e) => changeStatus.mutate({ id: c.id, status: e.target.value })}
                        className="border rounded px-2 py-1 text-xs"
                      >
                        <option value="active">Active</option>
                        <option value="suspended">Suspended</option>
                        <option value="deactivated">Deactivated</option>
                      </select>
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
