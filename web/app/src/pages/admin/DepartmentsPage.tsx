import { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Pencil } from 'lucide-react';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td, Tr } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Tooltip } from '../../components/ui/Tooltip';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { Department, PaginatedResponse, User } from '../../types';

interface BudgetData {
  department_id: string;
  allocated_amount_cents: number;
  spent_cents: number;
  remaining_cents: number;
  utilization_pct: number;
}

interface BudgetSummary {
  fiscal_year: number;
  total_allocated_cents: number;
  total_spent_cents: number;
  departments: BudgetData[];
}

interface EditModalState {
  deptId: string;
  deptName: string;
  managerUserId: string;
  priorityWeight: number;
  allocatedAmount: number;
  budgetEnforcementEnabled: boolean;
  originalManagerUserId: string | null;
}

function formatCents(cents: number): string {
  return `$${(cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function budgetColor(pct: number): string {
  if (pct >= 100) return 'text-destructive';
  if (pct >= 80) return 'text-warning';
  return 'text-success';
}

export default function DepartmentsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [page, setPage] = useState(1);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createError, setCreateError] = useState('');
  const [editModal, setEditModal] = useState<EditModalState | null>(null);
  const [editError, setEditError] = useState('');
  const [pendingDelete, setPendingDelete] = useState<{ id: string; name: string } | null>(null);

  const { data, isLoading, isError, error: listError, refetch } = useQuery({
    queryKey: ['departments', page],
    queryFn: async () => {
      const { data } = await api.get('/departments', { params: { page, page_size: 20 } });
      return data as PaginatedResponse<Department>;
    },
  });

  const { data: budgetSummary } = useQuery({
    queryKey: ['budget-summary'],
    queryFn: async () => {
      const { data } = await api.get('/budgets/summary');
      return data.data as BudgetSummary;
    },
  });

  const { data: users } = useQuery({
    queryKey: ['users-for-manager'],
    queryFn: async () => {
      const { data } = await api.get('/users', { params: { page: 1, page_size: 100 } });
      return (data as PaginatedResponse<User>).data;
    },
    enabled: editModal !== null,
  });

  const budgetByDept = useMemo(() => {
    const map = new Map<string, BudgetData>();
    budgetSummary?.departments?.forEach((b) => map.set(b.department_id, b));
    return map;
  }, [budgetSummary]);

  const activeUsers = useMemo(() => (users ?? []).filter((u) => u.is_active), [users]);

  const create = useMutation({
    mutationFn: (deptName: string) => api.post('/departments', { name: deptName }),
    onSuccess: () => {
      setCreateName('');
      setCreateError('');
      setCreateModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      showToast({ title: t('page.departments.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.departments.error_generic');
      setCreateError(detail);
      showToast({ title: t('page.departments.error_create_title'), description: detail, variant: 'error' });
    },
  });

  const saveEdit = useMutation({
    mutationFn: async (payload: EditModalState) => {
      const name = payload.deptName.trim();
      await api.put(`/departments/${payload.deptId}`, { name, priority_weight: payload.priorityWeight, budget_enforcement_enabled: payload.budgetEnforcementEnabled });

      const nextManager = payload.managerUserId || null;
      const previousManager = payload.originalManagerUserId;

      if (nextManager && nextManager !== previousManager) {
        await api.put(`/departments/${payload.deptId}/manager`, { user_id: nextManager });
      }
      if (!nextManager && previousManager) {
        await api.delete(`/departments/${payload.deptId}/manager`);
      }

      await api.put(`/departments/${payload.deptId}/budget`, {
        allocated_amount_cents: Math.round(payload.allocatedAmount * 100),
      });
    },
    onSuccess: () => {
      setEditModal(null);
      setEditError('');
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      queryClient.invalidateQueries({ queryKey: ['budget-summary'] });
      showToast({ title: t('page.departments.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.departments.error_update');
      setEditError(detail);
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

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (pendingDelete && !deleteDept.isPending) {
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
        setCreateError('');
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [create.isPending, createModalOpen, deleteDept.isPending, editModal, pendingDelete, saveEdit.isPending]);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.departments.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.departments.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setCreateName('');
            setCreateError('');
            setCreateModalOpen(true);
          }}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.departments.new')}
        </button>
      </div>

      {isLoading ? <Card><Loading /></Card> : isError ? (
        <Card>
          <ErrorState
            message={(listError as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => {
              void refetch();
            }}
          />
        </Card>
      ) : !data?.data.length ? (
        <Card>
          <EmptyState
            message={t('page.departments.empty')}
            action={(
              <button
                type="button"
                onClick={() => {
                  setCreateName('');
                  setCreateError('');
                  setCreateModalOpen(true);
                }}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
              >
                {t('page.departments.new')}
              </button>
            )}
          />
        </Card>
      ) : (
        <>
          <Table>
              <thead>
                <tr>
                  <Th>{t('table.name')}</Th>
                  <Th>{t('page.departments.manager')}</Th>
                  <Th>{t('page.departments.priority_weight')}</Th>
                  <Th>{t('page.departments.budget_allocated')}</Th>
                  <Th>{t('page.departments.budget_spent')}</Th>
                  <Th>{t('page.departments.budget_remaining')}</Th>
                  <Th className="text-right">{t('table.actions')}</Th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((d) => {
                  const budget = budgetByDept.get(d.id);
                  return (
                    <Tr key={d.id}>
                      <Td>{d.name}</Td>
                      <Td>{d.manager_name || d.manager_email || t('common.unassigned')}</Td>
                      <Td>{d.priority_weight ?? 0}</Td>
                      <Td>{budget ? formatCents(budget.allocated_amount_cents) : t('page.departments.no_budget')}</Td>
                      <Td>
                        {budget ? (
                          <span className={`text-xs ${budgetColor(budget.utilization_pct)}`}>
                            {formatCents(budget.spent_cents)} ({budget.utilization_pct}%)
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">-</span>
                        )}
                      </Td>
                      <Td>
                        {budget ? (
                          <span className={`text-xs ${budgetColor(budget.utilization_pct)}`}>
                            {formatCents(budget.remaining_cents)}
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">-</span>
                        )}
                      </Td>
                      <Td className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Tooltip content={t('common.edit')}>
                            <button
                              type="button"
                              onClick={() => {
                                setEditError('');
                                setEditModal({
                                  deptId: d.id,
                                  deptName: d.name,
                                  managerUserId: d.manager_user_id ?? '',
                                  priorityWeight: d.priority_weight ?? 0,
                                  allocatedAmount: budget ? budget.allocated_amount_cents / 100 : 0,
                                  budgetEnforcementEnabled: d.budget_enforcement_enabled ?? false,
                                  originalManagerUserId: d.manager_user_id ?? null,
                                });
                              }}
                              aria-label={t('common.edit')}
                              className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                            >
                              <Pencil className="h-4 w-4" />
                            </button>
                          </Tooltip>
                          <Tooltip content={t('common.delete')}>
                            <button
                              type="button"
                              onClick={() => setPendingDelete({ id: d.id, name: d.name })}
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
                  );
                })}
              </tbody>
          </Table>
          <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
        </>
      )}

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={t('page.departments.delete_title')}
        description={pendingDelete ? t('page.departments.delete_desc', { name: pendingDelete.name }) : ''}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={deleteDept.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete) deleteDept.mutate(pendingDelete.id);
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
              setCreateError('');
            }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.departments.new')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const name = createName.trim();
                if (!name) {
                  setCreateError(t('page.departments.error_name_required'));
                  return;
                }
                setCreateError('');
                create.mutate(name);
              }}
              className="mt-4 space-y-4"
            >
              <div>
                {createError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{createError}</div>}
                <label className="mb-1.5 block text-muted-foreground">{t('table.name')}</label>
                <input
                  type="text"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  className="w-full bg-card"
                  autoFocus
                  required
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (create.isPending) return;
                    setCreateModalOpen(false);
                    setCreateName('');
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
                if (!editModal.deptName.trim()) {
                  setEditError(t('page.departments.error_name_required'));
                  return;
                }
                if (editModal.priorityWeight < -1 || editModal.priorityWeight > 2) {
                  setEditError(t('page.departments.error_weight_range'));
                  return;
                }
                setEditError('');
                saveEdit.mutate(editModal);
              }}
              className="mt-4 space-y-4"
            >
              <div>
                {editError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{editError}</div>}
                <label className="mb-1.5 block text-muted-foreground">{t('table.name')}</label>
                <input
                  type="text"
                  value={editModal.deptName}
                  onChange={(e) => setEditModal({ ...editModal, deptName: e.target.value })}
                  className="w-full bg-card"
                  required
                />
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.departments.manager')}</label>
                <select
                  value={editModal.managerUserId}
                  onChange={(e) => setEditModal({ ...editModal, managerUserId: e.target.value })}
                  className="w-full bg-card"
                >
                  <option value="">{t('common.unassigned')}</option>
                  {activeUsers.map((u) => (
                    <option key={u.id} value={u.id}>{u.name || u.email}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.departments.priority_weight')}</label>
                <input
                  type="number"
                  min="-1"
                  max="2"
                  step="1"
                  value={editModal.priorityWeight}
                  onChange={(e) => setEditModal({ ...editModal, priorityWeight: Number(e.target.value) })}
                  className="w-full bg-card"
                />
                <p className="mt-1 text-xs text-muted-foreground">{t('page.departments.priority_weight_help')}</p>
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.departments.budget_amount')}</label>
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  value={editModal.allocatedAmount}
                  onChange={(e) => setEditModal({ ...editModal, allocatedAmount: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-card"
                />
              </div>
              <div className="flex items-center gap-3">
                <label className="relative inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    checked={editModal.budgetEnforcementEnabled}
                    onChange={(e) => setEditModal({ ...editModal, budgetEnforcementEnabled: e.target.checked })}
                    className="peer sr-only"
                  />
                  <div className="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary peer-focus:ring-2 peer-focus:ring-primary/50 after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full" />
                </label>
                <div>
                  <span className="text-sm text-foreground">{t('page.departments.budget_enforcement')}</span>
                  <p className="text-xs text-muted-foreground">{t('page.departments.budget_enforcement_help')}</p>
                </div>
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
