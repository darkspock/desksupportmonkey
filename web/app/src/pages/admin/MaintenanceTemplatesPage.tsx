import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { StatusBadge } from '../../components/ui/Badge';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { Table, Td, Th, Tr } from '../../components/ui/Table';
import { Tooltip } from '../../components/ui/Tooltip';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Pagination } from '../../components/ui/Pagination';
import { useToast } from '../../hooks/useToast';
import { useI18n, humanizeToken } from '../../lib/i18n';
import { formatDateTime } from '../../lib/date';
import type { Asset, AssetTypeDefinition, MaintenanceChecklistItem, MaintenancePlan, MaintenanceTemplate, PaginatedResponse } from '../../types';

interface ChecklistItemForm {
  title: string;
  description: string;
  is_required: boolean;
}

function emptyChecklistItem(): ChecklistItemForm {
  return { title: '', description: '', is_required: true };
}

export default function MaintenanceTemplatesPage() {
  const { t } = useI18n();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [planPage, setPlanPage] = useState(1);

  // Create modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createPriority, setCreatePriority] = useState('MEDIUM');
  const [createFrequency, setCreateFrequency] = useState('MONTHLY');
  const [createInterval, setCreateInterval] = useState(1);
  const [createAssetTypeFilter, setCreateAssetTypeFilter] = useState('');
  const [createChecklist, setCreateChecklist] = useState<ChecklistItemForm[]>([emptyChecklistItem()]);
  const [createError, setCreateError] = useState('');

  // Apply modal
  const [applyModalOpen, setApplyModalOpen] = useState(false);
  const [applyTemplateId, setApplyTemplateId] = useState('');
  const [applyAssetIds, setApplyAssetIds] = useState<string[]>([]);
  const [applyError, setApplyError] = useState('');

  // Confirm dialogs
  const [pendingTemplateDelete, setPendingTemplateDelete] = useState<MaintenanceTemplate | null>(null);
  const [pendingPlanDeactivate, setPendingPlanDeactivate] = useState<MaintenancePlan | null>(null);

  const { data: assetTypes } = useQuery({
    queryKey: ['asset-types-active'],
    queryFn: async () => {
      const { data } = await api.get('/asset-types', { params: { active_only: true } });
      return data.data as AssetTypeDefinition[];
    },
  });

  const { data: templates, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['maintenance-templates', page],
    queryFn: async () => {
      const { data } = await api.get('/maintenance-templates', { params: { page, page_size: 20 } });
      return data as PaginatedResponse<MaintenanceTemplate>;
    },
  });

  const { data: plans } = useQuery({
    queryKey: ['maintenance-plans', planPage],
    queryFn: async () => {
      const { data } = await api.get('/maintenance-plans', { params: { page: planPage, page_size: 20 } });
      return data as PaginatedResponse<MaintenancePlan>;
    },
  });

  const { data: assets } = useQuery({
    queryKey: ['assets-all-maintenance'],
    queryFn: async () => {
      const { data } = await api.get('/assets', { params: { page: 1, page_size: 100 } });
      return data as PaginatedResponse<Asset>;
    },
  });

  const assetLabelById = useMemo(
    () => new Map((assets?.data ?? []).map((a) => [a.id, `${a.brand} ${a.model} (${a.serial_number})`])),
    [assets],
  );

  const templateNameById = useMemo(
    () => new Map((templates?.data ?? []).map((tpl) => [tpl.id, tpl.name])),
    [templates],
  );

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['maintenance-templates'] });
    queryClient.invalidateQueries({ queryKey: ['maintenance-plans'] });
    queryClient.invalidateQueries({ queryKey: ['maintenance'] });
  };

  const create = useMutation({
    mutationFn: () => api.post('/maintenance-templates', {
      name: createName.trim(),
      default_priority: createPriority,
      recurrence_frequency: createFrequency,
      recurrence_interval: createInterval,
      asset_type_filter: createAssetTypeFilter || null,
      checklist_items: createChecklist
        .filter((c) => c.title.trim())
        .map((c) => ({ title: c.title.trim(), description: c.description.trim() || null, is_required: c.is_required })),
    }),
    onSuccess: () => {
      showToast({ title: t('page.maintenance_templates.toast_created'), variant: 'success' });
      resetCreateModal();
      invalidate();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.maintenance_templates.error_action');
      setCreateError(detail);
      showToast({ title: detail, variant: 'error' });
    },
  });

  const remove = useMutation({
    mutationFn: (templateId: string) => api.delete(`/maintenance-templates/${templateId}`),
    onSuccess: () => {
      invalidate();
      setPendingTemplateDelete(null);
      showToast({ title: t('page.maintenance_templates.toast_deleted'), variant: 'success' });
    },
    onError: () => showToast({ title: t('page.maintenance_templates.error_action'), variant: 'error' }),
  });

  const apply = useMutation({
    mutationFn: () => api.post(`/maintenance-templates/${applyTemplateId}/apply`, {
      asset_ids: applyAssetIds,
    }),
    onSuccess: () => {
      invalidate();
      showToast({ title: t('page.maintenance_templates.toast_applied'), variant: 'success' });
      resetApplyModal();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.maintenance_templates.error_action');
      setApplyError(detail);
      showToast({ title: detail, variant: 'error' });
    },
  });

  const deactivatePlan = useMutation({
    mutationFn: (planId: string) => api.delete(`/maintenance-plans/${planId}`),
    onSuccess: () => {
      invalidate();
      setPendingPlanDeactivate(null);
      showToast({ title: t('page.maintenance_templates.toast_plan_deactivated'), variant: 'success' });
    },
    onError: () => showToast({ title: t('page.maintenance_templates.error_action'), variant: 'error' }),
  });

  function resetCreateModal() {
    setCreateModalOpen(false);
    setCreateName('');
    setCreatePriority('MEDIUM');
    setCreateFrequency('MONTHLY');
    setCreateInterval(1);
    setCreateAssetTypeFilter('');
    setCreateChecklist([emptyChecklistItem()]);
    setCreateError('');
  }

  function resetApplyModal() {
    setApplyModalOpen(false);
    setApplyTemplateId('');
    setApplyAssetIds([]);
    setApplyError('');
  }

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (pendingTemplateDelete && !remove.isPending) { setPendingTemplateDelete(null); return; }
      if (pendingPlanDeactivate && !deactivatePlan.isPending) { setPendingPlanDeactivate(null); return; }
      if (applyModalOpen && !apply.isPending) { resetApplyModal(); return; }
      if (createModalOpen && !create.isPending) { resetCreateModal(); }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [apply.isPending, applyModalOpen, create.isPending, createModalOpen, deactivatePlan.isPending, pendingPlanDeactivate, pendingTemplateDelete, remove.isPending]);

  const formatRecurrence = (tpl: MaintenanceTemplate) => {
    if (!tpl.recurrence_frequency) return '—';
    const freq = t(`enum.recurrence.${tpl.recurrence_frequency.toLowerCase()}`);
    if (tpl.recurrence_interval <= 1) return freq;
    return `${t('page.maintenance_templates.every')} ${tpl.recurrence_interval} ${freq.toLowerCase()}`;
  };

  const formatChecklist = (items: MaintenanceChecklistItem[]) => {
    if (!items.length) return '—';
    return items.map((i) => i.title).join(', ');
  };

  function renderChecklistForm(items: ChecklistItemForm[], setItems: (items: ChecklistItemForm[]) => void) {
    return (
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-muted-foreground">{t('page.maintenance_templates.checklist_label')}</label>
          <button type="button" onClick={() => setItems([...items, emptyChecklistItem()])} className="text-xs text-primary hover:underline">
            {t('page.maintenance_templates.add_checklist_item')}
          </button>
        </div>
        <div className="space-y-3">
          {items.map((item, idx) => (
            <div key={idx} className="border rounded-lg p-3 bg-secondary">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block mb-1.5 text-muted-foreground text-xs">{t('table.name')}</label>
                  <input
                    type="text"
                    value={item.title}
                    onChange={(e) => { const next = [...items]; next[idx] = { ...item, title: e.target.value }; setItems(next); }}
                    placeholder={t('page.maintenance_templates.checklist_item_title')}
                    className="w-full text-sm"
                  />
                </div>
                <div>
                  <label className="block mb-1.5 text-muted-foreground text-xs">{t('page.maintenance_templates.description')}</label>
                  <input
                    type="text"
                    value={item.description}
                    onChange={(e) => { const next = [...items]; next[idx] = { ...item, description: e.target.value }; setItems(next); }}
                    placeholder={t('page.equipment_profiles.optional')}
                    className="w-full text-sm"
                  />
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between">
                <label className="flex items-center gap-2 text-xs text-muted-foreground">
                  <input
                    type="checkbox"
                    checked={item.is_required}
                    onChange={(e) => { const next = [...items]; next[idx] = { ...item, is_required: e.target.checked }; setItems(next); }}
                  />
                  {t('page.maintenance_templates.required')}
                </label>
                {items.length > 1 && (
                  <button type="button" onClick={() => setItems(items.filter((_, i) => i !== idx))} className="text-xs text-destructive hover:underline">
                    {t('page.maintenance_templates.remove_checklist_item')}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.maintenance_templates.title')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('page.maintenance_templates.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => { setApplyError(''); setApplyModalOpen(true); }}
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
          >
            {t('page.maintenance_templates.apply')}
          </button>
          <button
            type="button"
            onClick={() => { setCreateError(''); setCreateModalOpen(true); }}
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
          >
            {t('page.maintenance_templates.new')}
          </button>
        </div>
      </div>

      {/* Templates list */}
      <h3 className="mb-2 text-sm font-medium text-foreground">{t('page.maintenance_templates.templates')}</h3>
      {isLoading ? <Card><Loading /></Card> : isError ? (
        <Card>
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
            onRetry={() => { void refetch(); }}
          />
        </Card>
      ) : !(templates?.data.length) ? (
        <Card>
          <EmptyState
            message={t('common.no_data')}
            action={(
              <button
                type="button"
                onClick={() => { setCreateError(''); setCreateModalOpen(true); }}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
              >
                {t('page.maintenance_templates.new')}
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
                <Th>{t('table.priority')}</Th>
                <Th>{t('page.maintenance_templates.recurrence')}</Th>
                <Th>{t('page.maintenance_templates.checklist_label')}</Th>
                <Th>{t('table.status')}</Th>
                <Th className="text-right">{t('table.actions')}</Th>
              </tr>
            </thead>
            <tbody>
              {templates.data.map((tpl) => (
                <Tr key={tpl.id}>
                  <Td className="font-medium">{tpl.name}</Td>
                  <Td>{t(`enum.maintenance_priority.${tpl.default_priority.toLowerCase()}`)}</Td>
                  <Td>{formatRecurrence(tpl)}</Td>
                  <Td><span className="text-xs text-muted-foreground">{formatChecklist(tpl.checklist_items)}</span></Td>
                  <Td><StatusBadge status={tpl.is_active ? 'active' : 'deactivated'} /></Td>
                  <Td className="text-right">
                    <div className="flex items-center justify-end">
                      <Tooltip content={t('common.delete')}>
                        <button
                          type="button"
                          onClick={() => setPendingTemplateDelete(tpl)}
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
          <Pagination page={page} pageSize={20} total={templates.meta.total} onChange={setPage} />
        </>
      )}

      {/* Plans list */}
      <h3 className="mt-6 mb-2 text-sm font-medium text-foreground">{t('page.maintenance_templates.plans')}</h3>
      {!(plans?.data.length) ? (
        <Card>
          <EmptyState
            message={t('common.no_data')}
            action={(
              <button
                type="button"
                onClick={() => { setApplyError(''); setApplyModalOpen(true); }}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
              >
                {t('page.maintenance_templates.apply')}
              </button>
            )}
          />
        </Card>
      ) : (
        <>
          <Table>
            <thead>
              <tr>
                <Th>{t('table.asset')}</Th>
                <Th>{t('page.maintenance_templates.template')}</Th>
                <Th>{t('table.status')}</Th>
                <Th>{t('page.maintenance_templates.next_due')}</Th>
                <Th className="text-right">{t('table.actions')}</Th>
              </tr>
            </thead>
            <tbody>
              {plans.data.map((plan) => (
                <Tr key={plan.id}>
                  <Td>{assetLabelById.get(plan.asset_id) || plan.asset_id.slice(0, 8)}</Td>
                  <Td>{templateNameById.get(plan.template_id) || plan.template_id.slice(0, 8)}</Td>
                  <Td><StatusBadge status={plan.is_active ? 'active' : 'deactivated'} /></Td>
                  <Td>{formatDateTime(plan.next_due_at)}</Td>
                  <Td className="text-right">
                    <div className="flex items-center justify-end">
                      {plan.is_active && (
                        <Tooltip content={t('page.maintenance_templates.deactivate_plan')}>
                          <button
                            type="button"
                            onClick={() => setPendingPlanDeactivate(plan)}
                            aria-label={t('page.maintenance_templates.deactivate_plan')}
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-warning/40 text-warning hover:bg-warning/10 transition-colors"
                          >
                            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                              <circle cx="12" cy="12" r="10" />
                              <path d="m15 9-6 6M9 9l6 6" />
                            </svg>
                          </button>
                        </Tooltip>
                      )}
                    </div>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
          <Pagination page={planPage} pageSize={20} total={plans.meta.total} onChange={setPlanPage} />
        </>
      )}

      {/* Confirm: delete template */}
      <ConfirmDialog
        open={Boolean(pendingTemplateDelete)}
        title={t('page.maintenance_templates.delete_template_title')}
        description={pendingTemplateDelete ? t('page.maintenance_templates.delete_template_desc', { name: pendingTemplateDelete.name }) : ''}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={remove.isPending}
        onCancel={() => setPendingTemplateDelete(null)}
        onConfirm={() => {
          if (pendingTemplateDelete) remove.mutate(pendingTemplateDelete.id);
        }}
      />

      {/* Confirm: deactivate plan */}
      <ConfirmDialog
        open={Boolean(pendingPlanDeactivate)}
        title={t('page.maintenance_templates.deactivate_plan_title')}
        description={pendingPlanDeactivate ? t('page.maintenance_templates.deactivate_plan_desc', { id: pendingPlanDeactivate.id.slice(0, 8) }) : ''}
        confirmLabel={t('page.maintenance_templates.deactivate_plan')}
        busy={deactivatePlan.isPending}
        onCancel={() => setPendingPlanDeactivate(null)}
        onConfirm={() => {
          if (pendingPlanDeactivate) deactivatePlan.mutate(pendingPlanDeactivate.id);
        }}
      />

      {/* Create template modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => { if (!create.isPending) resetCreateModal(); }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-2xl rounded-xl border border-border bg-card p-6 shadow-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-foreground">{t('page.maintenance_templates.new')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!createName.trim()) { setCreateError(t('page.maintenance_templates.name_required')); return; }
                setCreateError('');
                create.mutate();
              }}
              className="mt-4 space-y-4"
            >
              {createError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{createError}</div>}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1.5 block text-muted-foreground">{t('table.name')}</label>
                  <input type="text" value={createName} onChange={(e) => setCreateName(e.target.value)} placeholder={t('table.name')} className="w-full bg-card" autoFocus required />
                </div>
                <div>
                  <label className="mb-1.5 block text-muted-foreground">{t('table.priority')}</label>
                  <select value={createPriority} onChange={(e) => setCreatePriority(e.target.value)} className="w-full bg-card">
                    {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((p) => <option key={p} value={p}>{t(`enum.maintenance_priority.${p.toLowerCase()}`)}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-muted-foreground">{t('page.maintenance_templates.frequency')}</label>
                  <select value={createFrequency} onChange={(e) => setCreateFrequency(e.target.value)} className="w-full bg-card">
                    {['DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY'].map((f) => <option key={f} value={f}>{t(`enum.recurrence.${f.toLowerCase()}`)}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-muted-foreground">{t('page.maintenance_templates.interval')}</label>
                  <input type="number" min={1} value={createInterval} onChange={(e) => setCreateInterval(Number(e.target.value || 1))} placeholder="1" className="w-full bg-card" />
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.maintenance_templates.asset_type_filter')}</label>
                <select value={createAssetTypeFilter} onChange={(e) => setCreateAssetTypeFilter(e.target.value)} className="w-full bg-card">
                  <option value="">{t('page.maintenance_templates.all_asset_types')}</option>
                  {(assetTypes ?? []).map((at) => <option key={at.code} value={at.code}>{at.name}</option>)}
                </select>
              </div>
              {renderChecklistForm(createChecklist, setCreateChecklist)}
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { if (!create.isPending) resetCreateModal(); }}
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

      {/* Apply template modal */}
      {applyModalOpen && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => { if (!apply.isPending) resetApplyModal(); }}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">{t('page.maintenance_templates.apply')}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!applyTemplateId) { setApplyError(t('page.maintenance_templates.select_template_required')); return; }
                if (!applyAssetIds.length) { setApplyError(t('page.maintenance_templates.select_assets_required')); return; }
                setApplyError('');
                apply.mutate();
              }}
              className="mt-4 space-y-4"
            >
              {applyError && <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">{applyError}</div>}
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.maintenance_templates.template')}</label>
                <select value={applyTemplateId} onChange={(e) => setApplyTemplateId(e.target.value)} className="w-full bg-card" required>
                  <option value="">{t('page.maintenance_templates.select_template')}</option>
                  {(templates?.data ?? []).map((tpl) => <option key={tpl.id} value={tpl.id}>{tpl.name}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-muted-foreground">{t('page.maintenance_templates.select_assets')}</label>
                <select
                  multiple
                  value={applyAssetIds}
                  onChange={(e) => setApplyAssetIds(Array.from(e.target.selectedOptions, (o) => o.value))}
                  className="w-full bg-card min-h-[120px]"
                >
                  {(assets?.data ?? []).map((a) => (
                    <option key={a.id} value={a.id}>{a.brand} {a.model} ({a.serial_number})</option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { if (!apply.isPending) resetApplyModal(); }}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={apply.isPending}
                  className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {apply.isPending ? t('common.working') : t('page.maintenance_templates.apply')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
