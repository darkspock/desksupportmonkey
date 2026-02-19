import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { Table, Td, Th, Tr } from '../../components/ui/Table';
import { Tooltip } from '../../components/ui/Tooltip';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Pagination } from '../../components/ui/Pagination';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import { formatDateTime } from '../../lib/date';
import type { Asset, MaintenancePlan, MaintenanceTemplate, PaginatedResponse } from '../../types';

export default function MaintenanceTemplatesPage() {
  const { t } = useI18n();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [planPage, setPlanPage] = useState(1);

  const [name, setName] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [frequency, setFrequency] = useState('MONTHLY');
  const [interval, setInterval] = useState(1);
  const [assetTypeFilter, setAssetTypeFilter] = useState('');
  const [checklistRaw, setChecklistRaw] = useState('');

  const [applyTemplateId, setApplyTemplateId] = useState('');
  const [applyAssetIds, setApplyAssetIds] = useState<string[]>([]);
  const [pendingTemplateDelete, setPendingTemplateDelete] = useState<MaintenanceTemplate | null>(null);
  const [pendingPlanDeactivate, setPendingPlanDeactivate] = useState<MaintenancePlan | null>(null);

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
      name,
      default_priority: priority,
      recurrence_frequency: frequency,
      recurrence_interval: interval,
      asset_type_filter: assetTypeFilter || null,
      checklist_items: checklistRaw.split('\n').map((v) => v.trim()).filter(Boolean).map((title) => ({ title, is_required: true })),
    }),
    onSuccess: () => {
      showToast({ title: t('page.maintenance_templates.toast_created'), variant: 'success' });
      setName('');
      setChecklistRaw('');
      invalidate();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.maintenance_templates.error_action');
      showToast({ title: detail, variant: 'error' });
    },
  });

  const remove = useMutation({
    mutationFn: (templateId: string) => api.delete(`/maintenance-templates/${templateId}`),
    onSuccess: () => { invalidate(); showToast({ title: t('page.maintenance_templates.toast_deleted'), variant: 'success' }); },
    onError: () => showToast({ title: t('page.maintenance_templates.error_action'), variant: 'error' }),
  });

  const apply = useMutation({
    mutationFn: () => api.post(`/maintenance-templates/${applyTemplateId}/apply`, {
      asset_ids: applyAssetIds,
    }),
    onSuccess: () => {
      invalidate();
      showToast({ title: t('page.maintenance_templates.toast_applied'), variant: 'success' });
      setApplyAssetIds([]);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.maintenance_templates.error_action');
      showToast({ title: detail, variant: 'error' });
    },
  });

  const deactivatePlan = useMutation({
    mutationFn: (planId: string) => api.delete(`/maintenance-plans/${planId}`),
    onSuccess: () => { invalidate(); showToast({ title: t('page.maintenance_templates.toast_plan_deactivated'), variant: 'success' }); },
    onError: () => showToast({ title: t('page.maintenance_templates.error_action'), variant: 'error' }),
  });

  /* Format interval + frequency for display, e.g. "Every 3 months" */
  const formatRecurrence = (tpl: MaintenanceTemplate) => {
    if (!tpl.recurrence_frequency) return '—';
    const freq = t(`enum.recurrence.${tpl.recurrence_frequency.toLowerCase()}`);
    if (tpl.recurrence_interval <= 1) return freq;
    return `${t('page.maintenance_templates.every')} ${tpl.recurrence_interval} ${freq.toLowerCase()}`;
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.maintenance_templates.title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.maintenance_templates.subtitle')}</p>
      </div>

      {/* Create form */}
      <Card>
        <h3 className="mb-3 text-sm font-medium text-foreground">{t('page.maintenance_templates.new')}</h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-muted-foreground">{t('table.name')}</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder={t('table.name')} />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-muted-foreground">{t('table.priority')}</label>
            <select value={priority} onChange={(e) => setPriority(e.target.value)}>
              {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((p) => <option key={p} value={p}>{t(`enum.maintenance_priority.${p.toLowerCase()}`)}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-muted-foreground">{t('page.maintenance_templates.frequency')}</label>
            <select value={frequency} onChange={(e) => setFrequency(e.target.value)}>
              {['DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY'].map((f) => <option key={f} value={f}>{t(`enum.recurrence.${f.toLowerCase()}`)}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-muted-foreground">{t('page.maintenance_templates.interval')}</label>
            <input type="number" min={1} value={interval} onChange={(e) => setInterval(Number(e.target.value || 1))} placeholder="1" />
          </div>
          <div className="flex flex-col gap-1 md:col-span-2">
            <label className="text-xs font-medium text-muted-foreground">{t('page.maintenance_templates.asset_type_filter')}</label>
            <input value={assetTypeFilter} onChange={(e) => setAssetTypeFilter(e.target.value)} placeholder={t('page.maintenance_templates.asset_type_filter')} />
          </div>
          <div className="flex flex-col gap-1 md:col-span-2">
            <label className="text-xs font-medium text-muted-foreground">{t('page.maintenance_templates.checklist_label')}</label>
            <textarea value={checklistRaw} onChange={(e) => setChecklistRaw(e.target.value)} rows={4} placeholder={t('page.maintenance_templates.checklist_help')} />
          </div>
        </div>
        <button
          onClick={() => {
            if (!name.trim()) {
              showToast({ title: t('page.maintenance_templates.name_required'), variant: 'error' });
              return;
            }
            create.mutate();
          }}
          disabled={create.isPending}
          className="mt-3 inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {t('common.create')}
        </button>
      </Card>

      {/* Apply template */}
      <Card>
        <h3 className="mb-3 text-sm font-medium text-foreground">{t('page.maintenance_templates.apply')}</h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-muted-foreground">{t('page.maintenance_templates.template')}</label>
            <select value={applyTemplateId} onChange={(e) => setApplyTemplateId(e.target.value)}>
              <option value="">{t('page.maintenance_templates.select_template')}</option>
              {(templates?.data ?? []).map((tpl) => <option key={tpl.id} value={tpl.id}>{tpl.name}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-muted-foreground">{t('page.maintenance_templates.select_assets')}</label>
            <select
              multiple
              value={applyAssetIds}
              onChange={(e) => setApplyAssetIds(Array.from(e.target.selectedOptions, (o) => o.value))}
              className="min-h-[80px]"
            >
              {(assets?.data ?? []).map((a) => (
                <option key={a.id} value={a.id}>{a.brand} {a.model} ({a.serial_number})</option>
              ))}
            </select>
          </div>
        </div>
        <button
          onClick={() => {
            if (!applyTemplateId) {
              showToast({ title: t('page.maintenance_templates.select_template_required'), variant: 'error' });
              return;
            }
            apply.mutate();
          }}
          disabled={apply.isPending}
          className="mt-3 inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
        >
          {t('page.maintenance_templates.apply')}
        </button>
      </Card>

      {/* Templates list */}
      <Card className="overflow-hidden p-0">
        <div className="p-5 pb-0">
          <h3 className="mb-3 text-sm font-medium text-foreground">{t('page.maintenance_templates.templates')}</h3>
        </div>
        {isLoading ? (
          <div className="p-5"><Loading /></div>
        ) : isError ? (
          <div className="p-5">
            <ErrorState
              message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail}
              onRetry={() => { void refetch(); }}
            />
          </div>
        ) : !(templates?.data.length) ? (
          <div className="p-5"><EmptyState message={t('common.no_data')} /></div>
        ) : (
          <>
            <Table>
              <thead>
                <tr className="hover:bg-transparent">
                  <Th className="pl-4">{t('table.name')}</Th>
                  <Th>{t('table.priority')}</Th>
                  <Th>{t('page.maintenance_templates.recurrence')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th className="pr-4"><span className="sr-only">{t('table.actions')}</span></Th>
                </tr>
              </thead>
              <tbody>
                {templates.data.map((tpl) => (
                  <Tr key={tpl.id}>
                    <Td className="pl-4 font-medium">{tpl.name}</Td>
                    <Td>{t(`enum.maintenance_priority.${tpl.default_priority.toLowerCase()}`)}</Td>
                    <Td>{formatRecurrence(tpl)}</Td>
                    <Td><Badge variant={tpl.is_active ? 'success' : 'default'}>{tpl.is_active ? t('enum.active') : t('enum.deactivated')}</Badge></Td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center justify-end">
                        <Tooltip content={t('common.delete')}>
                          <button
                            onClick={() => setPendingTemplateDelete(tpl)}
                            aria-label={t('common.delete')}
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-destructive hover:bg-destructive/10 transition-colors"
                          >
                            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                            </svg>
                          </button>
                        </Tooltip>
                      </div>
                    </td>
                  </Tr>
                ))}
              </tbody>
            </Table>
            <div className="p-4">
              <Pagination page={page} pageSize={20} total={templates.meta.total} onChange={setPage} />
            </div>
          </>
        )}
      </Card>

      {/* Plans list */}
      <Card className="overflow-hidden p-0">
        <div className="p-5 pb-0">
          <h3 className="mb-3 text-sm font-medium text-foreground">{t('page.maintenance_templates.plans')}</h3>
        </div>
        {!(plans?.data.length) ? (
          <div className="p-5"><EmptyState message={t('common.no_data')} /></div>
        ) : (
          <>
            <Table>
              <thead>
                <tr className="hover:bg-transparent">
                  <Th className="pl-4">{t('table.asset')}</Th>
                  <Th>{t('page.maintenance_templates.template')}</Th>
                  <Th>{t('table.status')}</Th>
                  <Th>{t('page.maintenance_templates.next_due')}</Th>
                  <Th className="pr-4"><span className="sr-only">{t('table.actions')}</span></Th>
                </tr>
              </thead>
              <tbody>
                {plans.data.map((plan) => (
                  <Tr key={plan.id}>
                    <Td className="pl-4">{assetLabelById.get(plan.asset_id) || plan.asset_id.slice(0, 8)}</Td>
                    <Td>{templateNameById.get(plan.template_id) || plan.template_id.slice(0, 8)}</Td>
                    <Td><Badge variant={plan.is_active ? 'success' : 'default'}>{plan.is_active ? t('enum.active') : t('enum.deactivated')}</Badge></Td>
                    <Td>{formatDateTime(plan.next_due_at)}</Td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center justify-end">
                        {plan.is_active && (
                          <Tooltip content={t('page.maintenance_templates.deactivate_plan')}>
                            <button
                              onClick={() => setPendingPlanDeactivate(plan)}
                              aria-label={t('page.maintenance_templates.deactivate_plan')}
                              className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                            >
                              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="10" />
                                <path d="m15 9-6 6M9 9l6 6" />
                              </svg>
                            </button>
                          </Tooltip>
                        )}
                      </div>
                    </td>
                  </Tr>
                ))}
              </tbody>
            </Table>
            <div className="p-4">
              <Pagination page={planPage} pageSize={20} total={plans.meta.total} onChange={setPlanPage} />
            </div>
          </>
        )}
      </Card>

      <ConfirmDialog
        open={Boolean(pendingTemplateDelete)}
        title={t('page.maintenance_templates.delete_template_title')}
        description={pendingTemplateDelete ? t('page.maintenance_templates.delete_template_desc', { name: pendingTemplateDelete.name }) : ''}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={remove.isPending}
        onCancel={() => setPendingTemplateDelete(null)}
        onConfirm={() => {
          if (!pendingTemplateDelete) return;
          remove.mutate(pendingTemplateDelete.id, { onSettled: () => setPendingTemplateDelete(null) });
        }}
      />

      <ConfirmDialog
        open={Boolean(pendingPlanDeactivate)}
        title={t('page.maintenance_templates.deactivate_plan_title')}
        description={pendingPlanDeactivate ? t('page.maintenance_templates.deactivate_plan_desc', { id: pendingPlanDeactivate.id.slice(0, 8) }) : ''}
        confirmLabel={t('page.maintenance_templates.deactivate_plan')}
        busy={deactivatePlan.isPending}
        onCancel={() => setPendingPlanDeactivate(null)}
        onConfirm={() => {
          if (!pendingPlanDeactivate) return;
          deactivatePlan.mutate(pendingPlanDeactivate.id, { onSettled: () => setPendingPlanDeactivate(null) });
        }}
      />
    </div>
  );
}
