import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { StatusBadge } from '../../components/ui/Badge';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Tooltip } from '../../components/ui/Tooltip';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { EmployeeRole, PaginatedResponse } from '../../types';

interface EditModalState {
  roleId: string;
  name: string;
  description: string;
}

export default function EmployeeRolesPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [page, setPage] = useState(1);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createDescription, setCreateDescription] = useState('');
  const [createError, setCreateError] = useState('');
  const [editModal, setEditModal] = useState<EditModalState | null>(null);
  const [editError, setEditError] = useState('');
  const [pendingDelete, setPendingDelete] = useState<{ id: string; name: string } | null>(null);

  const { data, isLoading, isError, error: listError, refetch } = useQuery({
    queryKey: ['employee-roles', page],
    queryFn: async () => {
      const { data } = await api.get('/employee-roles', { params: { page, page_size: 20 } });
      return data as PaginatedResponse<EmployeeRole>;
    },
  });

  const create = useMutation({
    mutationFn: () =>
      api.post('/employee-roles', { name: createName.trim(), description: createDescription.trim() || null }),
    onSuccess: () => {
      setCreateName('');
      setCreateDescription('');
      setCreateError('');
      setCreateModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['employee-roles'] });
      showToast({ title: t('page.employee_roles.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.employee_roles.error_generic');
      setCreateError(detail);
      showToast({ title: t('page.employee_roles.error_create_title'), description: detail, variant: 'error' });
    },
  });

  const saveEdit = useMutation({
    mutationFn: (payload: EditModalState) =>
      api.put(`/employee-roles/${payload.roleId}`, {
        name: payload.name.trim(),
        description: payload.description.trim() || null,
      }),
    onSuccess: () => {
      setEditModal(null);
      setEditError('');
      queryClient.invalidateQueries({ queryKey: ['employee-roles'] });
      showToast({ title: t('page.employee_roles.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.employee_roles.error_generic');
      setEditError(detail);
      showToast({ title: t('page.employee_roles.error_update_title'), description: detail, variant: 'error' });
    },
  });

  const deleteRole = useMutation({
    mutationFn: (id: string) => api.delete(`/employee-roles/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employee-roles'] });
      setPendingDelete(null);
      showToast({ title: t('page.employee_roles.toast_deleted'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.employee_roles.error_generic');
      showToast({ title: t('page.employee_roles.error_delete_title'), description: detail, variant: 'error' });
    },
  });

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (pendingDelete && !deleteRole.isPending) {
        setPendingDelete(null);
        return;
      }
      if (editModal && !saveEdit.isPending) {
        setEditModal(null);
        setEditError('');
        return;
      }
      if (createModalOpen && !create.isPending) {
        setCreateModalOpen(false);
        setCreateName('');
        setCreateDescription('');
        setCreateError('');
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [create.isPending, createModalOpen, deleteRole.isPending, editModal, pendingDelete, saveEdit.isPending]);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.employee_roles.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.employee_roles.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setCreateName('');
            setCreateDescription('');
            setCreateError('');
            setCreateModalOpen(true);
          }}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.employee_roles.new')}
        </button>
      </div>

      {isLoading ? <Card><Loading /></Card> : isError ? (
        <Card>
          <ErrorState
            message={(listError as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => { void refetch(); }}
          />
        </Card>
      ) : !data?.data.length ? (
        <Card>
          <EmptyState
            message={t('page.employee_roles.empty')}
            action={(
              <button
                type="button"
                onClick={() => {
                  setCreateName('');
                  setCreateDescription('');
                  setCreateError('');
                  setCreateModalOpen(true);
                }}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
              >
                {t('page.employee_roles.new')}
              </button>
            )}
          />
        </Card>
      ) : (
        <>
          <Table>
              <thead>
                <tr>
                  <Th>{t('page.employee_roles.name')}</Th>
                  <Th>{t('page.employee_roles.description')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th className="text-right">{t('table.actions')}</Th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((role) => (
                  <Tr key={role.id}>
                    <Td className="font-medium">{role.name}</Td>
                    <Td><span className="text-muted-foreground text-sm">{role.description || '-'}</span></Td>
                    <Td><StatusBadge status={role.is_active ? 'active' : 'deactivated'} /></Td>
                    <Td className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Tooltip content={t('common.edit')}>
                          <button
                            type="button"
                            onClick={() => {
                              setEditError('');
                              setEditModal({
                                roleId: role.id,
                                name: role.name,
                                description: role.description ?? '',
                              });
                            }}
                            aria-label={t('common.edit')}
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                          >
                            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M15.2 5.2 18.8 8.8" />
                              <path d="M4 20h3.4l10-10a2.5 2.5 0 0 0-3.5-3.5L4 16.5V20z" />
                            </svg>
                          </button>
                        </Tooltip>
                        <Tooltip content={t('common.delete')}>
                          <button
                            type="button"
                            onClick={() => setPendingDelete({ id: role.id, name: role.name })}
                            aria-label={t('common.delete')}
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-destructive/40 text-destructive hover:bg-destructive/10 transition-colors"
                          >
                            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M3 6h18" />
                              <path d="M8 6V4h8v2" />
                              <path d="M19 6l-1 14H6L5 6" />
                              <path d="M10 11v6M14 11v6" />
                            </svg>
                          </button>
                        </Tooltip>
                      </div>
                    </Td>
                  </Tr>
                ))}
              </tbody>
          </Table>
          <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
        </>
      )}

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={t('page.employee_roles.delete_title')}
        description={t('page.employee_roles.delete_desc')}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={deleteRole.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete) deleteRole.mutate(pendingDelete.id);
        }}
      />

      {createModalOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (create.isPending) return;
              setCreateModalOpen(false);
              setCreateName('');
              setCreateDescription('');
              setCreateError('');
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.employee_roles.new')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const name = createName.trim();
                if (!name) {
                  setCreateError(t('page.employee_roles.error_name_required'));
                  return;
                }
                setCreateError('');
                create.mutate();
              }}
              className="mt-4 space-y-4"
            >
              <div>
                {createError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{createError}</div>}
                <label className="mb-1.5 block text-muted-foreground">{t('page.employee_roles.name')}</label>
                <input
                  type="text"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  placeholder={t('page.employee_roles.name_placeholder')}
                  className="w-full bg-card"
                  autoFocus
                  required
                />
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.employee_roles.description')}</label>
                <input
                  type="text"
                  value={createDescription}
                  onChange={(e) => setCreateDescription(e.target.value)}
                  placeholder={t('page.employee_roles.description_placeholder')}
                  className="w-full bg-card"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (create.isPending) return;
                    setCreateModalOpen(false);
                    setCreateName('');
                    setCreateDescription('');
                    setCreateError('');
                  }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={create.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {create.isPending ? t('common.working') : t('common.create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editModal && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => {
              if (saveEdit.isPending) return;
              setEditModal(null);
              setEditError('');
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('common.edit')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!editModal.name.trim()) {
                  setEditError(t('page.employee_roles.error_name_required'));
                  return;
                }
                setEditError('');
                saveEdit.mutate(editModal);
              }}
              className="mt-4 space-y-4"
            >
              <div>
                {editError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{editError}</div>}
                <label className="mb-1.5 block text-muted-foreground">{t('page.employee_roles.name')}</label>
                <input
                  type="text"
                  value={editModal.name}
                  onChange={(e) => setEditModal({ ...editModal, name: e.target.value })}
                  className="w-full bg-card"
                  required
                />
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.employee_roles.description')}</label>
                <input
                  type="text"
                  value={editModal.description}
                  onChange={(e) => setEditModal({ ...editModal, description: e.target.value })}
                  className="w-full bg-card"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (saveEdit.isPending) return;
                    setEditModal(null);
                    setEditError('');
                  }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={saveEdit.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {saveEdit.isPending ? t('common.working') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
