import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../components/ui/Toast';
import type { CustomFieldDefinition } from '../../types';

type EntityType = 'asset' | 'request' | 'incident';
type FieldType = 'text' | 'number' | 'date' | 'select' | 'multi_select' | 'boolean' | 'file';

interface FieldForm {
  label: string;
  field_type: FieldType;
  description: string;
  required: boolean;
  visible_to_employees: boolean;
  options: string[];
}

const emptyForm = (): FieldForm => ({
  label: '',
  field_type: 'text',
  description: '',
  required: false,
  visible_to_employees: false,
  options: [],
});

const FIELD_TYPES: FieldType[] = ['text', 'number', 'date', 'select', 'multi_select', 'boolean', 'file'];

const FIELD_TYPE_BADGE: Record<FieldType, string> = {
  text: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  number: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  date: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  select: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  multi_select: 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200',
  boolean: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  file: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
};

interface BillingOverview {
  plan: string;
}

export default function CustomFieldsPage() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<EntityType>('asset');
  const [showModal, setShowModal] = useState(false);
  const [editingField, setEditingField] = useState<CustomFieldDefinition | null>(null);
  const [form, setForm] = useState<FieldForm>(emptyForm());
  const [deleteTarget, setDeleteTarget] = useState<CustomFieldDefinition | null>(null);

  // Plan gating: check billing to ensure enterprise plan
  const { data: billing, isLoading: billingLoading } = useQuery<BillingOverview>({
    queryKey: ['billing-overview'],
    queryFn: async () => {
      const { data } = await api.get('/billing/');
      return data as BillingOverview;
    },
  });

  const isEnterprise = billing?.plan === 'enterprise' || billing?.plan === 'open_source';

  // Fetch definitions for the active tab
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['custom-field-definitions', activeTab],
    queryFn: async () => {
      const { data } = await api.get('/custom-fields/definitions', {
        params: { entity_type: activeTab },
      });
      return data.data as CustomFieldDefinition[];
    },
    enabled: isEnterprise,
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, unknown> = {
        entity_type: activeTab,
        label: form.label,
        field_type: form.field_type,
        description: form.description || null,
        required: form.required,
        visible_to_employees: form.visible_to_employees,
      };
      if (['select', 'multi_select'].includes(form.field_type)) {
        body.options = form.options.filter((o) => o.trim());
      }
      await api.post('/custom-fields/definitions', body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom-field-definitions', activeTab] });
      toast.success(t('page.custom_fields.created'));
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
      if (!editingField) return;
      const body: Record<string, unknown> = {
        label: form.label,
        description: form.description || null,
        required: form.required,
        visible_to_employees: form.visible_to_employees,
      };
      if (['select', 'multi_select'].includes(editingField.field_type)) {
        body.options = form.options.filter((o) => o.trim());
      }
      await api.put(`/custom-fields/definitions/${editingField.id}`, body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom-field-definitions', activeTab] });
      toast.success(t('page.custom_fields.updated'));
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
      await api.delete(`/custom-fields/definitions/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom-field-definitions', activeTab] });
      toast.success(t('page.custom_fields.deleted'));
      setDeleteTarget(null);
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        t('common.error');
      toast.error(message);
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: async ({ id, is_active }: { id: string; is_active: boolean }) => {
      await api.patch(`/custom-fields/definitions/${id}/status`, { is_active });
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['custom-field-definitions', activeTab] });
      toast.success(
        variables.is_active ? t('page.custom_fields.activated') : t('page.custom_fields.deactivated'),
      );
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        t('common.error');
      toast.error(message);
    },
  });

  const reorderMutation = useMutation({
    mutationFn: async ({ id, direction }: { id: string; direction: 'up' | 'down' }) => {
      await api.post(`/custom-fields/definitions/${id}/reorder`, { direction });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom-field-definitions', activeTab] });
      toast.success(t('page.custom_fields.reordered'));
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
    setEditingField(null);
    setForm(emptyForm());
  };

  const openCreate = () => {
    setEditingField(null);
    setForm(emptyForm());
    setShowModal(true);
  };

  const openEdit = (field: CustomFieldDefinition) => {
    setEditingField(field);
    setForm({
      label: field.label,
      field_type: field.field_type,
      description: field.description || '',
      required: field.required,
      visible_to_employees: field.visible_to_employees,
      options: field.options || [],
    });
    setShowModal(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.label.trim()) return;
    if (editingField) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };

  const addOption = () => {
    setForm((prev) => ({ ...prev, options: [...prev.options, ''] }));
  };

  const removeOption = (index: number) => {
    setForm((prev) => ({ ...prev, options: prev.options.filter((_, i) => i !== index) }));
  };

  const updateOption = (index: number, value: string) => {
    setForm((prev) => {
      const next = [...prev.options];
      next[index] = value;
      return { ...prev, options: next };
    });
  };

  const tabs: { key: EntityType; label: string }[] = [
    { key: 'asset', label: t('page.custom_fields.tab_assets') },
    { key: 'request', label: t('page.custom_fields.tab_requests') },
    { key: 'incident', label: t('page.custom_fields.tab_incidents') },
  ];

  const isMutating = createMutation.isPending || updateMutation.isPending;

  if (billingLoading) {
    return <Loading />;
  }

  // Plan gating
  if (!isEnterprise) {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t('page.custom_fields.title')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {t('page.custom_fields.subtitle')}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 flex flex-col items-center gap-4 text-center">
          <svg viewBox="0 0 24 24" className="h-12 w-12 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
          </svg>
          <p className="text-gray-600 dark:text-gray-300 max-w-md">
            {t('page.custom_fields.plan_required')}
          </p>
          <a
            href="/billing"
            className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {t('page.billing.upgrade')}
          </a>
        </div>
      </div>
    );
  }

  const showOptionsEditor = ['select', 'multi_select'].includes(
    editingField ? editingField.field_type : form.field_type,
  );

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t('page.custom_fields.title')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {t('page.custom_fields.subtitle')}
          </p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          {t('page.custom_fields.add_field')}
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {isLoading && <Loading />}
      {isError && (
        <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />
      )}
      {data && data.length === 0 && (
        <EmptyState title={t('page.custom_fields.no_fields')} />
      )}

      {data && data.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('page.custom_fields.field_label')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('page.custom_fields.field_type')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('page.custom_fields.field_key')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('page.custom_fields.required')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('common.status')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('page.custom_fields.visible_to_employees')}
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {data.map((field, index) => (
                <tr key={field.id} className={!field.is_active ? 'opacity-50' : ''}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                    {field.label}
                    {field.description && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 font-normal">
                        {field.description}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${FIELD_TYPE_BADGE[field.field_type]}`}
                    >
                      {t(`page.custom_fields.type_${field.field_type}`)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-gray-600 dark:text-gray-400">
                    {field.field_key}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        field.required
                          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {field.required ? t('page.custom_fields.yes') : t('page.custom_fields.no')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        field.is_active
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {field.is_active
                        ? t('page.custom_fields.active')
                        : t('page.custom_fields.inactive')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        field.visible_to_employees
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {field.visible_to_employees
                        ? t('page.custom_fields.yes')
                        : t('page.custom_fields.no')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-right">
                    <div className="flex gap-2 justify-end items-center">
                      {/* Reorder */}
                      <button
                        onClick={() => reorderMutation.mutate({ id: field.id, direction: 'up' })}
                        disabled={index === 0 || reorderMutation.isPending}
                        title={t('page.custom_fields.move_up')}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-30 text-xs"
                      >
                        ↑
                      </button>
                      <button
                        onClick={() => reorderMutation.mutate({ id: field.id, direction: 'down' })}
                        disabled={index === data.length - 1 || reorderMutation.isPending}
                        title={t('page.custom_fields.move_down')}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-30 text-xs"
                      >
                        ↓
                      </button>
                      {/* Edit */}
                      <button
                        onClick={() => openEdit(field)}
                        className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
                      >
                        {t('common.edit')}
                      </button>
                      {/* Toggle active */}
                      <button
                        onClick={() =>
                          toggleActiveMutation.mutate({ id: field.id, is_active: !field.is_active })
                        }
                        className={`hover:underline text-xs ${
                          field.is_active
                            ? 'text-yellow-600 dark:text-yellow-400'
                            : 'text-green-600 dark:text-green-400'
                        }`}
                      >
                        {field.is_active
                          ? t('page.custom_fields.deactivate')
                          : t('page.custom_fields.activate')}
                      </button>
                      {/* Delete */}
                      <button
                        onClick={() => setDeleteTarget(field)}
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
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-5 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {editingField
                  ? t('page.custom_fields.edit_field')
                  : t('page.custom_fields.add_field')}
              </h2>
            </div>
            <form onSubmit={handleSubmit} className="p-5 flex flex-col gap-4">
              {/* Label */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('page.custom_fields.field_label')} *
                </label>
                <input
                  type="text"
                  value={form.label}
                  onChange={(e) => setForm({ ...form, label: e.target.value })}
                  required
                  maxLength={100}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
                />
              </div>

              {/* Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('page.custom_fields.field_type')} *
                </label>
                <select
                  value={form.field_type}
                  onChange={(e) =>
                    setForm({ ...form, field_type: e.target.value as FieldType, options: [] })
                  }
                  disabled={!!editingField}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {FIELD_TYPES.map((ft) => (
                    <option key={ft} value={ft}>
                      {t(`page.custom_fields.type_${ft}`)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('page.custom_fields.description')}
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={2}
                  maxLength={500}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white resize-none"
                />
              </div>

              {/* Options Editor (only for select / multi_select) */}
              {showOptionsEditor && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t('page.custom_fields.options')}
                  </label>
                  <div className="flex flex-col gap-2">
                    {form.options.map((opt, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <input
                          type="text"
                          value={opt}
                          onChange={(e) => updateOption(idx, e.target.value)}
                          className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-1.5 text-sm text-gray-900 dark:text-white"
                        />
                        <button
                          type="button"
                          onClick={() => removeOption(idx)}
                          className="text-red-500 hover:text-red-700 text-xs shrink-0"
                        >
                          {t('page.custom_fields.remove_option')}
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={addOption}
                    className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    + {t('page.custom_fields.add_option')}
                  </button>
                </div>
              )}

              {/* Checkboxes */}
              <div className="flex flex-col gap-2">
                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={form.required}
                    onChange={(e) => setForm({ ...form, required: e.target.checked })}
                    className="rounded border-gray-300"
                  />
                  {t('page.custom_fields.required')}
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={form.visible_to_employees}
                    onChange={(e) => setForm({ ...form, visible_to_employees: e.target.checked })}
                    className="rounded border-gray-300"
                  />
                  {t('page.custom_fields.visible_to_employees')}
                </label>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={isMutating}
                  className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {isMutating ? t('common.saving') : t('page.custom_fields.save')}
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="inline-flex items-center rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  {t('page.custom_fields.cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-5 flex flex-col gap-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t('page.custom_fields.delete_confirm')}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {t('page.custom_fields.delete_warning')}
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
