import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Table, Th, Td } from '../../components/ui/Table';
import { Card } from '../../components/ui/Card';
import { Pagination } from '../../components/ui/Pagination';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { StatusBadge } from '../../components/ui/Badge';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { useI18n, humanizeToken } from '../../lib/i18n';
import type { Department, EquipmentProfile, PaginatedResponse, AssetType } from '../../types';

const ASSET_TYPES: AssetType[] = ['laptop', 'desktop', 'phone', 'tablet', 'monitor', 'printer', 'other'];
const ROLES = ['employee', 'technician'];

interface ItemForm {
  asset_type: AssetType;
  quantity: number;
  preferred_brand: string;
  preferred_model: string;
  min_ram_gb: string;
  min_storage_gb: string;
}

function emptyItem(): ItemForm {
  return { asset_type: 'laptop', quantity: 1, preferred_brand: '', preferred_model: '', min_ram_gb: '', min_storage_gb: '' };
}

export default function EquipmentProfilesPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [page, setPage] = useState(1);
  const [filterDept, setFilterDept] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterActive, setFilterActive] = useState<'all' | 'active'>('active');

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formDept, setFormDept] = useState('');
  const [formRole, setFormRole] = useState('employee');
  const [formItems, setFormItems] = useState<ItemForm[]>([emptyItem()]);
  const [pendingDelete, setPendingDelete] = useState<{ id: string } | null>(null);

  const { data: departments } = useQuery({
    queryKey: ['departments-all'],
    queryFn: async () => {
      const { data } = await api.get('/departments', { params: { page: 1, page_size: 100 } });
      return (data as PaginatedResponse<Department>).data;
    },
  });

  const { data, isLoading, isError, error: listError, refetch } = useQuery({
    queryKey: ['equipment-profiles', page, filterDept, filterRole, filterActive],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (filterDept) params.department_id = filterDept;
      if (filterRole) params.role = filterRole;
      if (filterActive === 'active') params.is_active = true;
      const { data } = await api.get('/equipment-profiles', { params });
      return data as PaginatedResponse<EquipmentProfile>;
    },
  });

  const deptMap = new Map(departments?.map((d) => [d.id, d.name]) ?? []);

  function resetForm() {
    setShowForm(false);
    setEditingId(null);
    setFormDept('');
    setFormRole('employee');
    setFormItems([emptyItem()]);
  }

  function buildPayloadItems() {
    return formItems.map((i) => ({
      asset_type: i.asset_type,
      quantity: i.quantity,
      preferred_brand: i.preferred_brand || null,
      preferred_model: i.preferred_model || null,
      min_ram_gb: i.min_ram_gb ? Number(i.min_ram_gb) : null,
      min_storage_gb: i.min_storage_gb ? Number(i.min_storage_gb) : null,
    }));
  }

  const createProfile = useMutation({
    mutationFn: () =>
      api.post('/equipment-profiles', {
        department_id: formDept,
        role: formRole,
        items: buildPayloadItems(),
      }),
    onSuccess: () => {
      resetForm();
      queryClient.invalidateQueries({ queryKey: ['equipment-profiles'] });
      showToast({ title: t('page.equipment_profiles.toast_created'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.equipment_profiles.error_generic');
      showToast({ title: t('page.equipment_profiles.error_create_title'), description: detail, variant: 'error' });
    },
  });

  const updateProfile = useMutation({
    mutationFn: (id: string) => api.put(`/equipment-profiles/${id}`, { items: buildPayloadItems() }),
    onSuccess: () => {
      resetForm();
      queryClient.invalidateQueries({ queryKey: ['equipment-profiles'] });
      showToast({ title: t('page.equipment_profiles.toast_updated'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.equipment_profiles.error_generic');
      showToast({ title: t('page.equipment_profiles.error_update_title'), description: detail, variant: 'error' });
    },
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, activate }: { id: string; activate: boolean }) =>
      api.post(`/equipment-profiles/${id}/${activate ? 'activate' : 'deactivate'}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment-profiles'] });
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

  function startEdit(p: EquipmentProfile) {
    setEditingId(p.id);
    setFormDept(p.department_id);
    setFormRole(p.role);
    setFormItems(
      p.items.map((i) => ({
        asset_type: i.asset_type,
        quantity: i.quantity,
        preferred_brand: i.preferred_brand ?? '',
        preferred_model: i.preferred_model ?? '',
        min_ram_gb: i.min_ram_gb != null ? String(i.min_ram_gb) : '',
        min_storage_gb: i.min_storage_gb != null ? String(i.min_storage_gb) : '',
      })),
    );
    setShowForm(true);
  }

  function updateItem(index: number, field: keyof ItemForm, value: string | number) {
    setFormItems((prev) => prev.map((item, i) => (i === index ? { ...item, [field]: value } : item)));
  }

  function removeItem(index: number) {
    setFormItems((prev) => prev.filter((_, i) => i !== index));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (editingId) {
      updateProfile.mutate(editingId);
    } else {
      createProfile.mutate();
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.equipment_profiles.title')}</h2>
        <button
          onClick={() => { if (showForm) resetForm(); else setShowForm(true); }}
          className={showForm
            ? 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50'
            : 'inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50'}
        >
          {showForm ? t('common.close') : t('page.equipment_profiles.new')}
        </button>
      </div>

      {showForm && (
        <Card className="mb-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            {!editingId && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('table.department')}</label>
                  <select value={formDept} onChange={(e) => setFormDept(e.target.value)} required className="w-full bg-card">
                    <option value="">{t('page.equipment_profiles.select_department')}</option>
                    {departments?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground">{t('table.role')}</label>
                  <select value={formRole} onChange={(e) => setFormRole(e.target.value)} className="w-full bg-card">
                    {ROLES.map((r) => <option key={r} value={r}>{t(`enum.${r}`, undefined, { defaultValue: humanizeToken(r) })}</option>)}
                  </select>
                </div>
              </div>
            )}

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-muted-foreground">{t('page.equipment_profiles.items')}</label>
                <button type="button" onClick={() => setFormItems((prev) => [...prev, emptyItem()])} className="text-xs text-primary hover:underline">
                  {t('page.equipment_profiles.add_item')}
                </button>
              </div>

              <div className="space-y-3">
                {formItems.map((item, idx) => (
                  <div key={idx} className="border rounded-lg p-3 bg-secondary">
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="block mb-1.5 text-muted-foreground text-xs">{t('table.type')}</label>
                        <select value={item.asset_type} onChange={(e) => updateItem(idx, 'asset_type', e.target.value)} className="w-full text-sm">
                          {ASSET_TYPES.map((at) => <option key={at} value={at}>{t(`enum.${at}`, undefined, { defaultValue: humanizeToken(at) })}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="block mb-1.5 text-muted-foreground text-xs">{t('page.equipment_profiles.quantity')}</label>
                        <input type="number" min={1} max={100} value={item.quantity} onChange={(e) => updateItem(idx, 'quantity', Number(e.target.value))} className="w-full text-sm" />
                      </div>
                      <div>
                        <label className="block mb-1.5 text-muted-foreground text-xs">{t('table.brand')}</label>
                        <input value={item.preferred_brand} onChange={(e) => updateItem(idx, 'preferred_brand', e.target.value)} placeholder={t('page.equipment_profiles.optional')} className="w-full text-sm" />
                      </div>
                      <div>
                        <label className="block mb-1.5 text-muted-foreground text-xs">{t('table.model')}</label>
                        <input value={item.preferred_model} onChange={(e) => updateItem(idx, 'preferred_model', e.target.value)} placeholder={t('page.equipment_profiles.optional')} className="w-full text-sm" />
                      </div>
                      <div>
                        <label className="block mb-1.5 text-muted-foreground text-xs">{t('page.equipment_profiles.min_ram')}</label>
                        <input type="number" min={0} value={item.min_ram_gb} onChange={(e) => updateItem(idx, 'min_ram_gb', e.target.value)} placeholder="GB" className="w-full text-sm" />
                      </div>
                      <div>
                        <label className="block mb-1.5 text-muted-foreground text-xs">{t('page.equipment_profiles.min_storage')}</label>
                        <input type="number" min={0} value={item.min_storage_gb} onChange={(e) => updateItem(idx, 'min_storage_gb', e.target.value)} placeholder="GB" className="w-full text-sm" />
                      </div>
                    </div>
                    {formItems.length > 1 && (
                      <button type="button" onClick={() => removeItem(idx)} className="mt-2 text-xs text-destructive hover:underline">
                        {t('page.equipment_profiles.remove_item')}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={createProfile.isPending || updateProfile.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {editingId ? t('common.save') : t('common.create')}
            </button>
          </form>
        </Card>
      )}

      <div className="flex gap-3 mb-4 flex-wrap">
        <select value={filterDept} onChange={(e) => { setFilterDept(e.target.value); setPage(1); }} className="bg-card">
          <option value="">{t('page.equipment_profiles.all_departments')}</option>
          {departments?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <select value={filterRole} onChange={(e) => { setFilterRole(e.target.value); setPage(1); }} className="bg-card">
          <option value="">{t('page.equipment_profiles.all_roles')}</option>
          {ROLES.map((r) => <option key={r} value={r}>{t(`enum.${r}`, undefined, { defaultValue: humanizeToken(r) })}</option>)}
        </select>
        <select value={filterActive} onChange={(e) => { setFilterActive(e.target.value as 'all' | 'active'); setPage(1); }} className="bg-card">
          <option value="active">{t('page.equipment_profiles.active_only')}</option>
          <option value="all">{t('page.equipment_profiles.show_all')}</option>
        </select>
      </div>

      <Card>
        {isLoading ? <Loading /> : isError ? (
          <ErrorState
            message={(listError as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => { void refetch(); }}
          />
        ) : !data?.data.length ? (
          <EmptyState message={t('page.equipment_profiles.empty')} />
        ) : (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>{t('table.department')}</Th>
                  <Th>{t('table.role')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th>{t('page.equipment_profiles.items')}</Th>
                  <Th>{t('table.actions')}</Th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((p) => (
                  <tr key={p.id}>
                    <Td>{deptMap.get(p.department_id) ?? p.department_id}</Td>
                    <Td>{t(`enum.${p.role}`, undefined, { defaultValue: humanizeToken(p.role) })}</Td>
                    <Td><StatusBadge status={p.is_active ? 'active' : 'deactivated'} /></Td>
                    <Td>
                      <span className="text-xs text-muted-foreground">
                        {p.items.map((i) => `${i.quantity}x ${t(`enum.${i.asset_type}`, undefined, { defaultValue: humanizeToken(i.asset_type) })}`).join(', ')}
                      </span>
                    </Td>
                    <Td>
                      <div className="flex items-center gap-2">
                        <button onClick={() => startEdit(p)} className="text-xs text-primary hover:underline">{t('common.edit')}</button>
                        <button
                          onClick={() => toggleActive.mutate({ id: p.id, activate: !p.is_active })}
                          className={`text-xs hover:underline ${p.is_active ? 'text-warning' : 'text-success'}`}
                        >
                          {p.is_active ? t('page.equipment_profiles.deactivate') : t('page.equipment_profiles.activate')}
                        </button>
                        <button onClick={() => setPendingDelete({ id: p.id })} className="text-xs text-destructive hover:underline">{t('common.delete')}</button>
                      </div>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination page={page} pageSize={20} total={data.meta.total} onChange={setPage} />
          </>
        )}
      </Card>

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
    </div>
  );
}
