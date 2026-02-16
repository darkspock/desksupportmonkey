import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { formatDate } from '../../lib/date';
import { useI18n } from '../../lib/i18n';
import type { Department, PaginatedResponse } from '../../types';

export default function DepartmentsPage() {
  const { t } = useI18n();
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [pendingDelete, setPendingDelete] = useState<{ id: string; name: string } | null>(null);
  const [editing, setEditing] = useState<{ id: string; name: string } | null>(null);
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const { data, isLoading, isError, error: listError, refetch } = useQuery({
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
      showToast({ title: t('page.departments.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.departments.error_generic');
      setError(detail);
      showToast({ title: t('page.departments.error_create_title'), description: detail, variant: 'error' });
    },
  });

  const updateDept = useMutation({
    mutationFn: ({ id, deptName }: { id: string; deptName: string }) => api.put(`/departments/${id}`, { name: deptName }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      setEditing(null);
      showToast({ title: t('page.departments.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.departments.error_update');
      showToast({ title: t('page.departments.error_update_title'), description: detail, variant: 'error' });
    },
  });

  const deleteDept = useMutation({
    mutationFn: (id: string) => api.delete(`/departments/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      setPendingDelete(null);
      showToast({ title: t('page.departments.toast_deleted'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.departments.error_delete');
      showToast({ title: t('page.departments.error_delete_title'), description: detail, variant: 'error' });
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">{t('page.departments.title')}</h2>
        <button onClick={() => setShowForm(!showForm)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          {showForm ? t('common.cancel') : t('page.departments.new')}
        </button>
      </div>

      {showForm && (
        <Card className="mb-4">
          <form onSubmit={(e) => { e.preventDefault(); create.mutate(); }} className="flex gap-3 items-end">
            <div className="flex-1">
              {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('table.name')}</label>
              <input value={name} onChange={(e) => setName(e.target.value)} required className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <button type="submit" disabled={create.isPending} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">{t('common.create')}</button>
          </form>
        </Card>
      )}

      <Card>
        {isLoading ? <Loading /> : isError ? (
          <ErrorState
            message={(listError as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => {
              void refetch();
            }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.departments.empty')} />
        ) : (
          <>
            <Table>
              <thead><tr><Th>{t('table.name')}</Th><Th>{t('table.users')}</Th><Th>{t('table.created')}</Th><Th>{t('table.actions')}</Th></tr></thead>
              <tbody className="divide-y divide-gray-100">
                {data.data.map((d) => {
                  const isEditing = editing?.id === d.id;
                  return (
                    <tr key={d.id}>
                      <Td>
                        {isEditing ? (
                          <input
                            value={editing.name}
                            onChange={(e) => setEditing({ id: d.id, name: e.target.value })}
                            className="w-full border rounded px-2 py-1 text-xs"
                          />
                        ) : (
                          d.name
                        )}
                      </Td>
                      <Td>{d.user_count ?? '-'}</Td>
                      <Td>{formatDate(d.created_at)}</Td>
                      <Td>
                        <div className="flex items-center gap-2">
                          {isEditing ? (
                            <>
                              <button
                                onClick={() => updateDept.mutate({ id: d.id, deptName: editing.name })}
                                disabled={updateDept.isPending || !editing.name.trim()}
                                className="text-xs text-blue-600 hover:underline disabled:opacity-50"
                              >
                                {t('common.save')}
                              </button>
                              <button onClick={() => setEditing(null)} className="text-xs text-gray-600 hover:underline">
                                {t('common.cancel')}
                              </button>
                            </>
                          ) : (
                            <button onClick={() => setEditing({ id: d.id, name: d.name })} className="text-xs text-blue-600 hover:underline">{t('common.edit')}</button>
                          )}
                          <button onClick={() => setPendingDelete({ id: d.id, name: d.name })} className="text-xs text-red-600 hover:underline">{t('common.delete')}</button>
                        </div>
                      </Td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>
            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </>
        )}
      </Card>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={t('page.departments.delete_title')}
        description={pendingDelete ? t('page.departments.delete_desc', { name: pendingDelete.name }) : ''}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={deleteDept.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete) {
            deleteDept.mutate(pendingDelete.id);
          }
        }}
      />
    </div>
  );
}
