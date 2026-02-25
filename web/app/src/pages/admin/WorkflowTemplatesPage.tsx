import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Pencil } from 'lucide-react';
import api from '../../lib/api';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Table, Td, Th, Tr } from '../../components/ui/Table';
import { Tooltip } from '../../components/ui/Tooltip';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../components/ui/Toast';
import { WorkflowIcon } from '../../components/ui/WorkflowIcon';
import { LucideIconPickerModal } from '../../components/ui/LucideIconPickerModal';
import type { WorkflowTemplate } from '../../types';

interface SubtypeForm {
  id?: string;
  name: string;
  description: string;
  sort_order: number;
  is_active: boolean;
}

interface ChecklistItemForm {
  id?: string;
  title: string;
  description: string;
  is_required: boolean;
  sort_order: number;
}

interface TemplateForm {
  name: string;
  description: string;
  icon: string;
  require_all_complete: boolean;
  subtypes: SubtypeForm[];
  checklist_items: ChecklistItemForm[];
}

const emptyForm = (): TemplateForm => ({
  name: '',
  description: '',
  icon: '',
  require_all_complete: false,
  subtypes: [],
  checklist_items: [],
});

function normalizePayload(form: TemplateForm) {
  return {
    name: form.name.trim(),
    description: form.description.trim() || null,
    icon: form.icon.trim() || null,
    require_all_complete: form.require_all_complete,
    subtypes: form.subtypes
      .map((s) => ({
        id: s.id,
        name: s.name.trim(),
        description: s.description.trim() || null,
        is_active: s.is_active,
      }))
      .filter((s) => s.name.length > 0)
      .map((s, idx) => ({ ...s, sort_order: idx })),
    checklist_items: form.checklist_items
      .map((item) => ({
        id: item.id,
        title: item.title.trim(),
        description: item.description.trim() || null,
        is_required: item.is_required,
      }))
      .filter((item) => item.title.length > 0)
      .map((item, idx) => ({ ...item, sort_order: idx })),
  };
}

const iconActionButtonClass =
  'inline-flex h-8 w-8 items-center justify-center rounded-md border transition-colors';

export default function WorkflowTemplatesPage() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [showModal, setShowModal] = useState(false);
  const [iconPickerOpen, setIconPickerOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<WorkflowTemplate | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<WorkflowTemplate | null>(null);
  const [toggleTarget, setToggleTarget] = useState<{
    id: string;
    name: string;
    nextActive: boolean;
  } | null>(null);
  const [form, setForm] = useState<TemplateForm>(emptyForm());
  const [formError, setFormError] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['workflow-templates'],
    queryFn: async () => {
      const { data } = await api.get('/workflow-templates');
      return data.data as WorkflowTemplate[];
    },
  });

  const extractError = (err: unknown): string => {
    const data = (err as { response?: { data?: { detail?: string; error?: { message?: string } } } })?.response?.data;
    return data?.error?.message || data?.detail || t('common.error');
  };

  const createMutation = useMutation({
    mutationFn: async () => {
      await api.post('/workflow-templates', normalizePayload(form));
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow-templates'] });
      toast.success(t('page.workflow_templates.toast_created'));
      closeModal(true);
    },
    onError: (err: unknown) => {
      toast.error(extractError(err));
    },
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!editingTemplate) return;
      await api.put(`/workflow-templates/${editingTemplate.id}`, normalizePayload(form));
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow-templates'] });
      toast.success(t('page.workflow_templates.toast_updated'));
      closeModal(true);
    },
    onError: (err: unknown) => {
      toast.error(extractError(err));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/workflow-templates/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow-templates'] });
      toast.success(t('page.workflow_templates.toast_deleted'));
      setDeleteTarget(null);
    },
    onError: (err: unknown) => {
      const msg = extractError(err);
      if (msg.toLowerCase().includes('request')) {
        toast.error(t('page.workflow_templates.has_requests'));
      } else {
        toast.error(msg);
      }
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: async ({ id, is_active }: { id: string; is_active: boolean }) => {
      await api.put(`/workflow-templates/${id}`, { is_active });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow-templates'] });
    },
    onError: (err: unknown) => {
      toast.error(extractError(err));
    },
  });

  const isMutating = createMutation.isPending || updateMutation.isPending;

  const closeModal = (force = false) => {
    if (!force && isMutating) return;
    setShowModal(false);
    setIconPickerOpen(false);
    setEditingTemplate(null);
    setForm(emptyForm());
    setFormError('');
  };

  const openCreate = () => {
    setEditingTemplate(null);
    setForm(emptyForm());
    setFormError('');
    setShowModal(true);
  };

  const openEdit = (tmpl: WorkflowTemplate) => {
    setEditingTemplate(tmpl);
    setForm({
      name: tmpl.name,
      description: tmpl.description || '',
      icon: tmpl.icon || '',
      require_all_complete: tmpl.require_all_complete,
      subtypes: tmpl.subtypes.map((s) => ({
        id: s.id,
        name: s.name,
        description: s.description || '',
        sort_order: s.sort_order,
        is_active: s.is_active,
      })),
      checklist_items: tmpl.checklist_items.map((item) => ({
        id: item.id,
        title: item.title,
        description: item.description || '',
        is_required: item.is_required,
        sort_order: item.sort_order,
      })),
    });
    setFormError('');
    setShowModal(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setFormError(t('page.workflow_templates.error_name_required'));
      return;
    }
    setFormError('');
    if (editingTemplate) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };

  const addSubtype = () => {
    setForm((prev) => ({
      ...prev,
      subtypes: [...prev.subtypes, { name: '', description: '', sort_order: prev.subtypes.length, is_active: true }],
    }));
  };

  const removeSubtype = (index: number) => {
    setForm((prev) => ({
      ...prev,
      subtypes: prev.subtypes.filter((_, i) => i !== index),
    }));
  };

  const updateSubtype = (index: number, field: keyof SubtypeForm, value: string) => {
    setForm((prev) => {
      const next = [...prev.subtypes];
      next[index] = { ...next[index], [field]: value };
      return { ...prev, subtypes: next };
    });
  };

  const addChecklistItem = () => {
    setForm((prev) => ({
      ...prev,
      checklist_items: [
        ...prev.checklist_items,
        { title: '', description: '', is_required: true, sort_order: prev.checklist_items.length },
      ],
    }));
  };

  const removeChecklistItem = (index: number) => {
    setForm((prev) => ({
      ...prev,
      checklist_items: prev.checklist_items.filter((_, i) => i !== index),
    }));
  };

  const updateChecklistItem = (
    index: number,
    field: keyof ChecklistItemForm,
    value: string | boolean,
  ) => {
    setForm((prev) => {
      const next = [...prev.checklist_items];
      next[index] = { ...next[index], [field]: value };
      return { ...prev, checklist_items: next };
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {t('page.workflow_templates.title')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('page.workflow_templates.subtitle')}
          </p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90"
        >
          {t('page.workflow_templates.new')}
        </button>
      </div>

      {isLoading && (
        <Card>
          <Loading />
        </Card>
      )}

      {isError && (
        <Card>
          <ErrorState
            message={
              (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
              t('common.error')
            }
            onRetry={() => {
              void refetch();
            }}
          />
        </Card>
      )}

      {data && data.length === 0 && (
        <Card>
          <EmptyState message={t('page.workflow_templates.empty')} />
        </Card>
      )}

      {data && data.length > 0 && (
        <Table>
          <thead>
            <tr>
              <Th>{t('page.workflow_templates.name')}</Th>
              <Th>{t('page.workflow_templates.icon')}</Th>
              <Th>{t('page.workflow_templates.subtypes')}</Th>
              <Th>{t('page.workflow_templates.checklist_items')}</Th>
              <Th>{t('common.status')}</Th>
              <Th className="text-right">{t('table.actions')}</Th>
            </tr>
          </thead>
          <tbody>
            {data.map((tmpl) => (
              <Tr key={tmpl.id} className={!tmpl.is_active ? 'opacity-70' : undefined}>
                <Td className="font-medium text-foreground">
                  {tmpl.name}
                  {tmpl.description && (
                    <p className="mt-0.5 text-xs font-normal text-muted-foreground">{tmpl.description}</p>
                  )}
                </Td>
                <Td>
                  {tmpl.icon ? (
                    <div className="flex items-center gap-1.5">
                      <WorkflowIcon name={tmpl.icon} className="h-4 w-4 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">{tmpl.icon}</span>
                    </div>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </Td>
                <Td className="text-muted-foreground">
                  {tmpl.subtypes.length > 0
                    ? t('page.workflow_templates.subtypes_count', { count: tmpl.subtypes.length })
                    : '—'}
                </Td>
                <Td className="text-muted-foreground">
                  {tmpl.checklist_items.length > 0
                    ? t('page.workflow_templates.items_count', { count: tmpl.checklist_items.length })
                    : '—'}
                </Td>
                <Td>
                  <Badge variant={tmpl.is_active ? 'success' : 'default'}>
                    {tmpl.is_active
                      ? t('page.workflow_templates.active')
                      : t('page.workflow_templates.inactive')}
                  </Badge>
                </Td>
                <Td className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Tooltip content={t('common.edit')}>
                      <button
                        type="button"
                        aria-label={t('common.edit')}
                        onClick={() => openEdit(tmpl)}
                        className={`${iconActionButtonClass} border-border bg-background text-foreground hover:bg-accent`}
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                    </Tooltip>

                    <Tooltip
                      content={
                        tmpl.is_active
                          ? t('page.workflow_templates.deactivate')
                          : t('page.workflow_templates.activate')
                      }
                    >
                      <button
                        type="button"
                        aria-label={
                          tmpl.is_active
                            ? t('page.workflow_templates.deactivate')
                            : t('page.workflow_templates.activate')
                        }
                        onClick={() =>
                          setToggleTarget({
                            id: tmpl.id,
                            name: tmpl.name,
                            nextActive: !tmpl.is_active,
                          })
                        }
                        className={`${iconActionButtonClass} border-border bg-background text-foreground hover:bg-accent`}
                      >
                        {tmpl.is_active ? (
                          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="6" y="4" width="12" height="16" rx="1" />
                            <path d="M9 20h6" />
                          </svg>
                        ) : (
                          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M7 4v16l13-8Z" />
                          </svg>
                        )}
                      </button>
                    </Tooltip>

                    <Tooltip content={t('common.delete')}>
                      <button
                        type="button"
                        aria-label={t('common.delete')}
                        onClick={() => setDeleteTarget(tmpl)}
                        className={`${iconActionButtonClass} border-destructive/40 bg-background text-destructive hover:bg-destructive/10`}
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
      )}

      {showModal && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => closeModal()}
            aria-label={t('errors.close_confirmation_dialog')}
          />
          <div className="relative z-[91] w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">
              {editingTemplate ? `${t('common.edit')} ${editingTemplate.name}` : t('page.workflow_templates.new')}
            </h3>

            <form onSubmit={handleSubmit} className="mt-4 space-y-5">
              {formError && (
                <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                  {formError}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="mb-1.5 block text-sm text-muted-foreground">
                    {t('page.workflow_templates.name')} *
                  </label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    maxLength={255}
                    required
                    autoFocus
                    className="w-full bg-card"
                    placeholder="Employee Offboarding"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-sm text-muted-foreground">
                    {t('page.workflow_templates.icon')}
                  </label>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setIconPickerOpen(true)}
                      className="inline-flex items-center justify-center rounded-md h-9 px-3 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all"
                    >
                      {form.icon
                        ? t('page.workflow_templates.change_icon')
                        : t('page.workflow_templates.select_icon')}
                    </button>
                    {form.icon && (
                      <button
                        type="button"
                        onClick={() => setForm({ ...form, icon: '' })}
                        className="inline-flex items-center justify-center rounded-md h-9 px-3 text-sm font-medium border border-destructive/40 bg-background text-destructive hover:bg-destructive/10 transition-all"
                      >
                        {t('page.workflow_templates.remove_icon')}
                      </button>
                    )}
                  </div>
                  {form.icon && (
                    <div className="mt-2 inline-flex items-center gap-2 rounded-md border border-border bg-secondary/40 px-2.5 py-1.5 text-xs text-foreground">
                      <WorkflowIcon name={form.icon} className="h-3.5 w-3.5" />
                      <span>{form.icon}</span>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-sm text-muted-foreground">
                  {t('page.workflow_templates.description')}
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  maxLength={500}
                  className="w-full resize-none bg-card"
                />
              </div>

              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <input
                  type="checkbox"
                  checked={form.require_all_complete}
                  onChange={(e) => setForm({ ...form, require_all_complete: e.target.checked })}
                />
                {t('page.workflow_templates.require_all_complete')}
              </label>

              <div>
                <label className="mb-1 block text-sm text-muted-foreground">
                  {t('page.workflow_templates.subtypes')}
                </label>
                <p className="mb-2 text-xs text-muted-foreground">
                  {t('page.workflow_templates.subtypes_hint')}
                </p>

                <div className="space-y-2">
                  {form.subtypes.map((sub, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={sub.name}
                        onChange={(e) => updateSubtype(idx, 'name', e.target.value)}
                        placeholder={t('page.workflow_templates.subtype_name')}
                        className="flex-1 bg-card"
                      />
                      <button
                        type="button"
                        onClick={() => removeSubtype(idx)}
                        className="inline-flex items-center justify-center rounded-md h-8 px-2.5 text-xs font-medium border border-destructive/40 bg-background text-destructive hover:bg-destructive/10"
                      >
                        {t('common.remove')}
                      </button>
                    </div>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={addSubtype}
                  className="mt-2 inline-flex items-center justify-center rounded-md h-8 px-2.5 text-xs font-medium border border-border bg-background text-foreground hover:bg-accent"
                >
                  + {t('page.workflow_templates.add_subtype')}
                </button>
              </div>

              <div>
                <label className="mb-1 block text-sm text-muted-foreground">
                  {t('page.workflow_templates.checklist_items')}
                </label>
                <p className="mb-2 text-xs text-muted-foreground">
                  {t('page.workflow_templates.checklist_hint')}
                </p>

                <div className="space-y-3">
                  {form.checklist_items.map((item, idx) => (
                    <div key={idx} className="rounded-lg border border-border bg-secondary/40 p-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={item.title}
                          onChange={(e) => updateChecklistItem(idx, 'title', e.target.value)}
                          placeholder={t('page.workflow_templates.item_title')}
                          className="flex-1 bg-card"
                        />
                        <button
                          type="button"
                          onClick={() => removeChecklistItem(idx)}
                          className="inline-flex items-center justify-center rounded-md h-8 px-2.5 text-xs font-medium border border-destructive/40 bg-background text-destructive hover:bg-destructive/10"
                        >
                          {t('common.remove')}
                        </button>
                      </div>
                      <input
                        type="text"
                        value={item.description}
                        onChange={(e) => updateChecklistItem(idx, 'description', e.target.value)}
                        placeholder={t('page.workflow_templates.item_description')}
                        className="mt-2 w-full bg-card"
                      />
                      <label className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                        <input
                          type="checkbox"
                          checked={item.is_required}
                          onChange={(e) => updateChecklistItem(idx, 'is_required', e.target.checked)}
                        />
                        {t('page.workflow_templates.item_required')}
                      </label>
                    </div>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={addChecklistItem}
                  className="mt-2 inline-flex items-center justify-center rounded-md h-8 px-2.5 text-xs font-medium border border-border bg-background text-foreground hover:bg-accent"
                >
                  + {t('page.workflow_templates.add_checklist_item')}
                </button>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => closeModal()}
                  disabled={isMutating}
                  className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={isMutating}
                  className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
                >
                  {isMutating ? t('common.saving') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <LucideIconPickerModal
        open={iconPickerOpen}
        selectedIcon={form.icon}
        onClose={() => setIconPickerOpen(false)}
        onSelect={(iconName) => {
          setForm((prev) => ({ ...prev, icon: iconName }));
          setIconPickerOpen(false);
        }}
      />

      <ConfirmDialog
        open={Boolean(toggleTarget)}
        title={t('page.workflow_templates.confirm_status_title')}
        description={
          toggleTarget
            ? toggleTarget.nextActive
              ? t('page.workflow_templates.confirm_activate', { name: toggleTarget.name })
              : t('page.workflow_templates.confirm_deactivate', { name: toggleTarget.name })
            : ''
        }
        confirmLabel={t('common.confirm')}
        busy={toggleActiveMutation.isPending}
        onCancel={() => setToggleTarget(null)}
        onConfirm={() => {
          if (!toggleTarget) return;
          toggleActiveMutation.mutate({
            id: toggleTarget.id,
            is_active: toggleTarget.nextActive,
          });
          setToggleTarget(null);
        }}
      />

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title={t('common.delete')}
        description={deleteTarget ? `${t('page.workflow_templates.confirm_delete')} (${deleteTarget.name})` : ''}
        confirmLabel={t('common.delete')}
        tone="danger"
        busy={deleteMutation.isPending}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => {
          if (deleteTarget) deleteMutation.mutate(deleteTarget.id);
        }}
      />
    </div>
  );
}
