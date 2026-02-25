import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../components/ui/Toast';
import type { WorkflowTemplate } from '../../types';

interface SubtypeForm {
  name: string;
  description: string;
  sort_order: number;
}

interface ChecklistItemForm {
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

export default function WorkflowTemplatesPage() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [showModal, setShowModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<WorkflowTemplate | null>(null);
  const [form, setForm] = useState<TemplateForm>(emptyForm());
  const [deleteTarget, setDeleteTarget] = useState<WorkflowTemplate | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['workflow-templates'],
    queryFn: async () => {
      const { data } = await api.get('/workflow-templates');
      return data.data as WorkflowTemplate[];
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      await api.post('/workflow-templates', {
        name: form.name,
        description: form.description || null,
        icon: form.icon || null,
        require_all_complete: form.require_all_complete,
        subtypes: form.subtypes.map((s, i) => ({
          name: s.name,
          description: s.description || null,
          sort_order: i,
        })),
        checklist_items: form.checklist_items.map((item, i) => ({
          title: item.title,
          description: item.description || null,
          is_required: item.is_required,
          sort_order: i,
        })),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow-templates'] });
      toast.success(t('page.workflow_templates.toast_created'));
      closeModal();
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        t('common.error');
      toast.error(message);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!editingTemplate) return;
      await api.put(`/workflow-templates/${editingTemplate.id}`, {
        name: form.name,
        description: form.description || null,
        icon: form.icon || null,
        require_all_complete: form.require_all_complete,
        subtypes: form.subtypes.map((s, i) => ({
          name: s.name,
          description: s.description || null,
          sort_order: i,
        })),
        checklist_items: form.checklist_items.map((item, i) => ({
          title: item.title,
          description: item.description || null,
          is_required: item.is_required,
          sort_order: i,
        })),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow-templates'] });
      toast.success(t('page.workflow_templates.toast_updated'));
      closeModal();
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        t('common.error');
      toast.error(message);
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
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '';
      if (detail.toLowerCase().includes('request')) {
        toast.error(t('page.workflow_templates.has_requests'));
      } else {
        toast.error(detail || t('common.error'));
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
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        t('common.error');
      toast.error(message);
    },
  });

  const closeModal = () => {
    setShowModal(false);
    setEditingTemplate(null);
    setForm(emptyForm());
  };

  const openCreate = () => {
    setEditingTemplate(null);
    setForm(emptyForm());
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
        name: s.name,
        description: s.description || '',
        sort_order: s.sort_order,
      })),
      checklist_items: tmpl.checklist_items.map((item) => ({
        title: item.title,
        description: item.description || '',
        is_required: item.is_required,
        sort_order: item.sort_order,
      })),
    });
    setShowModal(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    if (editingTemplate) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };

  // Subtype helpers
  const addSubtype = () => {
    setForm((prev) => ({
      ...prev,
      subtypes: [...prev.subtypes, { name: '', description: '', sort_order: prev.subtypes.length }],
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

  // Checklist item helpers
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

  const isMutating = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t('page.workflow_templates.title')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {t('page.workflow_templates.subtitle')}
          </p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          {t('page.workflow_templates.new')}
        </button>
      </div>

      {/* Content */}
      {isLoading && <Loading />}
      {isError && (
        <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />
      )}
      {data && data.length === 0 && (
        <EmptyState message={t('page.workflow_templates.empty')} />
      )}

      {data && data.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('page.workflow_templates.name')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('page.workflow_templates.subtypes')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('page.workflow_templates.checklist_items')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('common.status')}
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {data.map((tmpl) => (
                <tr key={tmpl.id} className={!tmpl.is_active ? 'opacity-50' : ''}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                    {tmpl.name}
                    {tmpl.description && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 font-normal">
                        {tmpl.description}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {tmpl.subtypes.length > 0
                      ? t('page.workflow_templates.subtypes_count').replace(
                          '{{count}}',
                          String(tmpl.subtypes.length),
                        )
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {tmpl.checklist_items.length > 0
                      ? t('page.workflow_templates.items_count').replace(
                          '{{count}}',
                          String(tmpl.checklist_items.length),
                        )
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        tmpl.is_active
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {tmpl.is_active
                        ? t('page.workflow_templates.active')
                        : t('page.workflow_templates.inactive')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-right">
                    <div className="flex gap-2 justify-end items-center">
                      <button
                        onClick={() => openEdit(tmpl)}
                        className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
                      >
                        {t('common.edit')}
                      </button>
                      <button
                        onClick={() =>
                          toggleActiveMutation.mutate({
                            id: tmpl.id,
                            is_active: !tmpl.is_active,
                          })
                        }
                        className={`hover:underline text-xs ${
                          tmpl.is_active
                            ? 'text-yellow-600 dark:text-yellow-400'
                            : 'text-green-600 dark:text-green-400'
                        }`}
                      >
                        {tmpl.is_active
                          ? t('page.workflow_templates.inactive')
                          : t('page.workflow_templates.active')}
                      </button>
                      <button
                        onClick={() => setDeleteTarget(tmpl)}
                        className="text-red-600 dark:text-red-400 hover:underline text-xs"
                      >
                        {t('common.delete')}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create / Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-5 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {editingTemplate
                  ? t('common.edit') + ' ' + editingTemplate.name
                  : t('page.workflow_templates.new')}
              </h2>
            </div>
            <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-5">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('page.workflow_templates.name')} *
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  maxLength={255}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
                  placeholder="e.g. Employee Offboarding"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('page.workflow_templates.description')}
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={2}
                  maxLength={500}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white resize-none"
                />
              </div>

              {/* Require all complete */}
              <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input
                  type="checkbox"
                  checked={form.require_all_complete}
                  onChange={(e) => setForm({ ...form, require_all_complete: e.target.checked })}
                  className="rounded border-gray-300"
                />
                {t('page.workflow_templates.require_all_complete')}
              </label>

              {/* Subtypes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('page.workflow_templates.subtypes')}
                </label>
                <p className="text-xs text-gray-400 dark:text-gray-500 mb-2">
                  {t('page.workflow_templates.subtypes_hint')}
                </p>
                <div className="flex flex-col gap-2">
                  {form.subtypes.map((sub, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={sub.name}
                        onChange={(e) => updateSubtype(idx, 'name', e.target.value)}
                        placeholder={t('page.workflow_templates.subtype_name')}
                        className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-1.5 text-sm text-gray-900 dark:text-white"
                      />
                      <button
                        type="button"
                        onClick={() => removeSubtype(idx)}
                        className="text-red-500 hover:text-red-700 text-xs shrink-0"
                      >
                        {t('common.remove')}
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={addSubtype}
                  className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  + {t('page.workflow_templates.add_subtype')}
                </button>
              </div>

              {/* Checklist Items */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('page.workflow_templates.checklist_items')}
                </label>
                <p className="text-xs text-gray-400 dark:text-gray-500 mb-2">
                  {t('page.workflow_templates.checklist_hint')}
                </p>
                <div className="flex flex-col gap-3">
                  {form.checklist_items.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex flex-col gap-1.5 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900"
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={item.title}
                          onChange={(e) => updateChecklistItem(idx, 'title', e.target.value)}
                          placeholder={t('page.workflow_templates.item_title')}
                          className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-1.5 text-sm text-gray-900 dark:text-white"
                        />
                        <button
                          type="button"
                          onClick={() => removeChecklistItem(idx)}
                          className="text-red-500 hover:text-red-700 text-xs shrink-0"
                        >
                          {t('common.remove')}
                        </button>
                      </div>
                      <input
                        type="text"
                        value={item.description}
                        onChange={(e) => updateChecklistItem(idx, 'description', e.target.value)}
                        placeholder={t('page.workflow_templates.item_description')}
                        className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-1.5 text-sm text-gray-900 dark:text-white"
                      />
                      <label className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                        <input
                          type="checkbox"
                          checked={item.is_required}
                          onChange={(e) =>
                            updateChecklistItem(idx, 'is_required', e.target.checked)
                          }
                          className="rounded border-gray-300"
                        />
                        {t('page.workflow_templates.item_required')}
                      </label>
                    </div>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={addChecklistItem}
                  className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  + {t('page.workflow_templates.add_checklist_item')}
                </button>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={isMutating}
                  className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {isMutating ? t('common.saving') : t('common.save')}
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="inline-flex items-center rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  {t('common.cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-5 flex flex-col gap-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t('common.delete')}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {t('page.workflow_templates.confirm_delete')}
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => deleteMutation.mutate(deleteTarget.id)}
                disabled={deleteMutation.isPending}
                className="inline-flex items-center rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {deleteMutation.isPending ? t('common.working') : t('common.delete')}
              </button>
              <button
                onClick={() => setDeleteTarget(null)}
                className="inline-flex items-center rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
