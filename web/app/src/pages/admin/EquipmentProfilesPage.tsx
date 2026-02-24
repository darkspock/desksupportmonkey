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
import { useI18n, humanizeToken } from '../../lib/i18n';
import type { AssetTypeDefinition, Department, EmployeeRole, EquipmentProfile, PaginatedResponse } from '../../types';

interface ItemForm {
  asset_type: string;
  quantity: number;
  preferred_brand: string;
  preferred_model: string;
  min_ram_gb: string;
  min_storage_gb: string;
  budget: string;
}

function emptyItem(defaultCode = ''): ItemForm {
  return { asset_type: defaultCode, quantity: 1, preferred_brand: '', preferred_model: '', min_ram_gb: '', min_storage_gb: '', budget: '' };
}

interface CreateModalState {
  deptId: string;
  roleId: string;
  items: ItemForm[];
}

interface EditModalState {
  profileId: string;
  deptId: string;
  roleId: string;
  items: ItemForm[];
}

export default function EquipmentProfilesPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [page, setPage] = useState(1);
  const [filterDept, setFilterDept] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterActive, setFilterActive] = useState<'all' | 'active'>('active');

  const [createModal, setCreateModal] = useState<CreateModalState | null>(null);
  const [createError, setCreateError] = useState('');
  const [editModal, setEditModal] = useState<EditModalState | null>(null);
  const [editError, setEditError] = useState('');
  const [pendingDelete, setPendingDelete] = useState<{ id: string } | null>(null);
  const [pendingToggle, setPendingToggle] = useState<{ id: string; activate: boolean; label: string } | null>(null);

  const { data: assetTypes } = useQuery({
    queryKey: ['asset-types-active'],
    queryFn: async () => {
      const { data } = await api.get('/asset-types', { params: { active_only: true } });
      return data.data as AssetTypeDefinition[];
    },
  });

  const { data: departments } = useQuery({
    queryKey: ['departments-all'],
    queryFn: async () => {
      const { data } = await api.get('/departments', { params: { page: 1, page_size: 100 } });
      return (data as PaginatedResponse<Department>).data;
    },
  });

  const { data: employeeRoles } = useQuery({
    queryKey: ['employee-roles-all'],
    queryFn: async () => {
      const { data } = await api.get('/employee-roles', { params: { page: 1, page_size: 100 } });
      return (data as PaginatedResponse<EmployeeRole>).data;
    },
  });

  const { data, isLoading, isError, error: listError, refetch } = useQuery({
    queryKey: ['equipment-profiles', page, filterDept, filterRole, filterActive],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (filterDept) params.department_id = filterDept;
      if (filterRole) params.employee_role_id = filterRole;
      if (filterActive === 'active') params.is_active = true;
      const { data } = await api.get('/equipment-profiles', { params });
      return data as PaginatedResponse<EquipmentProfile>;
    },
  });

  const deptMap = new Map(departments?.map((d) => [d.id, d.name]) ?? []);
  const roleMap = new Map(employeeRoles?.map((r) => [r.id, r.name]) ?? []);

  function buildPayloadItems(items: ItemForm[]) {
    return items.map((i) => ({
      asset_type: i.asset_type,
      quantity: i.quantity,
      preferred_brand: i.preferred_brand || null,
      preferred_model: i.preferred_model || null,
      min_ram_gb: i.min_ram_gb ? Number(i.min_ram_gb) : null,
      min_storage_gb: i.min_storage_gb ? Number(i.min_storage_gb) : null,
      budget_cents: i.budget ? Math.round(Number(i.budget) * 100) : null,
    }));
  }

  const createProfile = useMutation({
    mutationFn: (payload: CreateModalState) =>
      api.post('/equipment-profiles', {
        department_id: payload.deptId,
        employee_role_id: payload.roleId,
        items: buildPayloadItems(payload.items),
      }),
    onSuccess: () => {
      setCreateModal(null);
      setCreateError('');
      queryClient.invalidateQueries({ queryKey: ['equipment-profiles'] });
      showToast({ title: t('page.equipment_profiles.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.equipment_profiles.error_generic');
      setCreateError(detail);
      showToast({ title: t('page.equipment_profiles.error_create_title'), description: detail, variant: 'error' });
    },
  });

  const updateProfile = useMutation({
    mutationFn: (payload: EditModalState) =>
      api.put(`/equipment-profiles/${payload.profileId}`, { items: buildPayloadItems(payload.items) }),
    onSuccess: () => {
      setEditModal(null);
      setEditError('');
      queryClient.invalidateQueries({ queryKey: ['equipment-profiles'] });
      showToast({ title: t('page.equipment_profiles.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.equipment_profiles.error_generic');
      setEditError(detail);
      showToast({ title: t('page.equipment_profiles.error_update_title'), description: detail, variant: 'error' });
    },
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, activate }: { id: string; activate: boolean }) =>
      api.post(`/equipment-profiles/${id}/${activate ? 'activate' : 'deactivate'}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment-profiles'] });
      setPendingToggle(null);
      showToast({ title: t('page.equipment_profiles.toast_toggled'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.equipment_profiles.error_generic');
      showToast({ title: t('page.equipment_profiles.error_toggle_title'), description: detail, variant: 'error' });
    },
  });

  const deleteProfile = useMutation({
    mutationFn: (id: string) => api.delete(`/equipment-profiles/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment-profiles'] });
      setPendingDelete(null);
      showToast({ title: t('page.equipment_profiles.toast_deleted'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.equipment_profiles.error_generic');
      showToast({ title: t('page.equipment_profiles.error_delete_title'), description: detail, variant: 'error' });
    },
  });

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (pendingDelete && !deleteProfile.isPending) { setPendingDelete(null); return; }
      if (pendingToggle && !toggleActive.isPending) { setPendingToggle(null); return; }
      if (editModal && !updateProfile.isPending) { setEditModal(null); setEditError(''); return; }
      if (createModal && !createProfile.isPending) { setCreateModal(null); setCreateError(''); }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [createModal, createProfile.isPending, deleteProfile.isPending, editModal, pendingDelete, pendingToggle, toggleActive.isPending, updateProfile.isPending]);

  function renderItemsForm(items: ItemForm[], setItems: (items: ItemForm[]) => void) {
    return (
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-muted-foreground">{t('page.equipment_profiles.items')}</label>
          <button type="button" onClick={() => setItems([...items, emptyItem(assetTypes?.[0]?.code)])} className="text-xs text-primary hover:underline">
            {t('page.equipment_profiles.add_item')}
          </button>
        </div>
        <div className="space-y-3">
          {items.map((item, idx) => (
            <div key={idx} className="border rounded-lg p-3 bg-secondary">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block mb-1.5 text-muted-foreground text-xs">{t('table.type')}</label>
                  <select value={item.asset_type} onChange={(e) => { const next = [...items]; next[idx] = { ...item, asset_type: e.target.value }; setItems(next); }} className="w-full text-sm">
                    {(assetTypes ?? []).map((at) => <option key={at.code} value={at.code}>{at.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground text-xs">{t('page.equipment_profiles.quantity')}</label>
                  <input type="number" min={1} max={100} value={item.quantity} onChange={(e) => { const next = [...items]; next[idx] = { ...item, quantity: Number(e.target.value) }; setItems(next); }} className="w-full text-sm" />
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground text-xs">{t('table.brand')}</label>
                  <input value={item.preferred_brand} onChange={(e) => { const next = [...items]; next[idx] = { ...item, preferred_brand: e.target.value }; setItems(next); }} placeholder={t('page.equipment_profiles.optional')} className="w-full text-sm" />
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground text-xs">{t('table.model')}</label>
                  <input value={item.preferred_model} onChange={(e) => { const next = [...items]; next[idx] = { ...item, preferred_model: e.target.value }; setItems(next); }} placeholder={t('page.equipment_profiles.optional')} className="w-full text-sm" />
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground text-xs">{t('page.equipment_profiles.min_ram')}</label>
                  <input type="number" min={0} value={item.min_ram_gb} onChange={(e) => { const next = [...items]; next[idx] = { ...item, min_ram_gb: e.target.value }; setItems(next); }} placeholder="GB" className="w-full text-sm" />
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground text-xs">{t('page.equipment_profiles.min_storage')}</label>
                  <input type="number" min={0} value={item.min_storage_gb} onChange={(e) => { const next = [...items]; next[idx] = { ...item, min_storage_gb: e.target.value }; setItems(next); }} placeholder="GB" className="w-full text-sm" />
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground text-xs">{t('page.equipment_profiles.budget')}</label>
                  <input type="number" min={0} step={0.01} value={item.budget} onChange={(e) => { const next = [...items]; next[idx] = { ...item, budget: e.target.value }; setItems(next); }} placeholder="$" className="w-full text-sm" />
                </div>
              </div>
              {items.length > 1 && (
                <button type="button" onClick={() => setItems(items.filter((_, i) => i !== idx))} className="mt-2 text-xs text-destructive hover:underline">
                  {t('page.equipment_profiles.remove_item')}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.equipment_profiles.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.equipment_profiles.subtitle')}</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setCreateError('');
            setCreateModal({ deptId: '', roleId: '', items: [emptyItem(assetTypes?.[0]?.code)] });
          }}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.equipment_profiles.new')}
        </button>
      </div>

      <div className="flex gap-3 mb-4 flex-wrap">
        <select value={filterDept} onChange={(e) => { setFilterDept(e.target.value); setPage(1); }} className="bg-card">
          <option value="">{t('page.equipment_profiles.all_departments')}</option>
          {departments?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <select value={filterRole} onChange={(e) => { setFilterRole(e.target.value); setPage(1); }} className="bg-card">
          <option value="">{t('page.equipment_profiles.all_roles')}</option>
          {employeeRoles?.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
        </select>
        <select value={filterActive} onChange={(e) => { setFilterActive(e.target.value as 'all' | 'active'); setPage(1); }} className="bg-card">
          <option value="active">{t('page.equipment_profiles.active_only')}</option>
          <option value="all">{t('page.equipment_profiles.show_all')}</option>
        </select>
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
            message={t('page.equipment_profiles.empty')}
            action={(
              <button
                type="button"
                onClick={() => {
                  setCreateError('');
                  setCreateModal({ deptId: '', roleId: '', items: [emptyItem(assetTypes?.[0]?.code)] });
                }}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
              >
                {t('page.equipment_profiles.new')}
              </button>
            )}
          />
        </Card>
      ) : (
        <>
          <Table>
            <thead>
              <tr>
                <Th>{t('table.department')}</Th>
                <Th>{t('table.role')}</Th>
                <Th>{t('table.status')}</Th>
                <Th>{t('page.equipment_profiles.items')}</Th>
                <Th className="text-right">{t('table.actions')}</Th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((p) => (
                <Tr key={p.id}>
                  <Td>{deptMap.get(p.department_id) ?? p.department_id}</Td>
                  <Td>{roleMap.get(p.employee_role_id) ?? p.employee_role_id}</Td>
                  <Td><StatusBadge status={p.is_active ? 'active' : 'deactivated'} /></Td>
                  <Td>
                    <span className="text-xs text-muted-foreground">
                      {p.items.map((i) => {
                        const typeName = assetTypes?.find((at) => at.code === i.asset_type)?.name ?? humanizeToken(i.asset_type);
                        const name = `${i.quantity}x ${typeName}`;
                        return i.budget_cents != null ? `${name} ($${(i.budget_cents / 100).toFixed(0)})` : name;
                      }).join(', ')}
                    </span>
                  </Td>
                  <Td className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Tooltip content={t('common.edit')}>
                        <button
                          type="button"
                          onClick={() => {
                            setEditError('');
                            setEditModal({
                              profileId: p.id,
                              deptId: p.department_id,
                              roleId: p.employee_role_id,
                              items: p.items.map((i) => ({
                                asset_type: i.asset_type,
                                quantity: i.quantity,
                                preferred_brand: i.preferred_brand ?? '',
                                preferred_model: i.preferred_model ?? '',
                                min_ram_gb: i.min_ram_gb != null ? String(i.min_ram_gb) : '',
                                min_storage_gb: i.min_storage_gb != null ? String(i.min_storage_gb) : '',
                                budget: i.budget_cents != null ? String(i.budget_cents / 100) : '',
                              })),
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
                      <Tooltip content={p.is_active ? t('page.equipment_profiles.deactivate') : t('page.equipment_profiles.activate')}>
                        <button
                          type="button"
                          onClick={() => setPendingToggle({
                            id: p.id,
                            activate: !p.is_active,
                            label: p.is_active ? t('page.equipment_profiles.deactivate') : t('page.equipment_profiles.activate'),
                          })}
                          aria-label={p.is_active ? t('page.equipment_profiles.deactivate') : t('page.equipment_profiles.activate')}
                          className={`inline-flex h-8 w-8 items-center justify-center rounded-md border transition-colors ${p.is_active ? 'border-warning/40 text-warning hover:bg-warning/10' : 'border-success/40 text-success hover:bg-success/10'}`}
                        >
                          {p.is_active ? (
                            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M18.36 6.64A9 9 0 0 1 20.77 15" />
                              <path d="M6.16 6.16a9 9 0 1 0 12.68 12.68" />
                              <line x1="2" y1="2" x2="22" y2="22" />
                            </svg>
                          ) : (
                            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                              <polyline points="22 4 12 14.01 9 11.01" />
                            </svg>
                          )}
                        </button>
                      </Tooltip>
                      <Tooltip content={t('common.delete')}>
                        <button
                          type="button"
                          onClick={() => setPendingDelete({ id: p.id })}
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
        title={t('page.equipment_profiles.delete_title')}
        description={t('page.equipment_profiles.delete_desc')}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={deleteProfile.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete) deleteProfile.mutate(pendingDelete.id);
        }}
      />

      <ConfirmDialog
        open={Boolean(pendingToggle)}
        title={pendingToggle?.label ?? ''}
        description={t('page.equipment_profiles.toggle_desc')}
        confirmLabel={pendingToggle?.label ?? t('common.confirm')}
        tone={pendingToggle?.activate ? 'default' : 'danger'}
        busy={toggleActive.isPending}
        onCancel={() => setPendingToggle(null)}
        onConfirm={() => {
          if (pendingToggle) toggleActive.mutate({ id: pendingToggle.id, activate: pendingToggle.activate });
        }}
      />

      {createModal && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => { if (!createProfile.isPending) { setCreateModal(null); setCreateError(''); } }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-2xl rounded-xl border border-border bg-card p-6 shadow-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-foreground">{t('page.equipment_profiles.new')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!createModal.deptId) { setCreateError(t('page.equipment_profiles.error_dept_required')); return; }
                if (!createModal.roleId) { setCreateError(t('page.equipment_profiles.error_role_required')); return; }
                setCreateError('');
                createProfile.mutate(createModal);
              }}
              className="mt-4 space-y-4"
            >
              {createError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{createError}</div>}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('table.department')}</label>
                  <select value={createModal.deptId} onChange={(e) => setCreateModal({ ...createModal, deptId: e.target.value })} required className="w-full bg-card">
                    <option value="">{t('page.equipment_profiles.select_department')}</option>
                    {departments?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('table.role')}</label>
                  <select value={createModal.roleId} onChange={(e) => setCreateModal({ ...createModal, roleId: e.target.value })} required className="w-full bg-card">
                    <option value="">{t('page.equipment_profiles.select_role')}</option>
                    {employeeRoles?.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
                  </select>
                </div>
              </div>
              {renderItemsForm(createModal.items, (items) => setCreateModal({ ...createModal, items }))}
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { if (!createProfile.isPending) { setCreateModal(null); setCreateError(''); } }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={createProfile.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {createProfile.isPending ? t('common.working') : t('common.create')}
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
            onClick={() => { if (!updateProfile.isPending) { setEditModal(null); setEditError(''); } }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-2xl rounded-xl border border-border bg-card p-6 shadow-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-foreground">{t('common.edit')}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {deptMap.get(editModal.deptId) ?? editModal.deptId} / {roleMap.get(editModal.roleId) ?? editModal.roleId}
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setEditError('');
                updateProfile.mutate(editModal);
              }}
              className="mt-4 space-y-4"
            >
              {editError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{editError}</div>}
              {renderItemsForm(editModal.items, (items) => setEditModal({ ...editModal, items }))}
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { if (!updateProfile.isPending) { setEditModal(null); setEditError(''); } }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={updateProfile.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {updateProfile.isPending ? t('common.working') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
