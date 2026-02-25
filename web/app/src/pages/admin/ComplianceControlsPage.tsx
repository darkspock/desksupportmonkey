import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { Badge } from '../../components/ui/Badge';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../components/ui/Toast';
import type { ComplianceControl } from '../../types';

interface ControlForm {
  code: string;
  name: string;
  framework: string;
  description: string;
}

const emptyForm: ControlForm = { code: '', name: '', framework: '', description: '' };

export default function ComplianceControlsPage() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<ControlForm>(emptyForm);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['compliance-controls'],
    queryFn: async () => {
      const { data } = await api.get('/audit/controls');
      return data.data as ComplianceControl[];
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      await api.post('/audit/controls', {
        code: form.code,
        name: form.name,
        framework: form.framework,
        description: form.description || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance-controls'] });
      toast.success(t('audit.controls.created'));
      resetForm();
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      toast.error(message);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      await api.put(`/audit/controls/${editingId}`, {
        name: form.name,
        description: form.description || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance-controls'] });
      toast.success(t('audit.controls.updated'));
      resetForm();
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      toast.error(message);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/audit/controls/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance-controls'] });
      toast.success(t('audit.controls.deactivated'));
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      toast.error(message);
    },
  });

  const resetForm = () => {
    setShowForm(false);
    setEditingId(null);
    setForm(emptyForm);
  };

  const startEdit = (control: ComplianceControl) => {
    setEditingId(control.id);
    setForm({
      code: control.code,
      name: control.name,
      framework: control.framework,
      description: control.description || '',
    });
    setShowForm(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.code.trim() || !form.name.trim() || !form.framework.trim()) return;
    if (editingId) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('audit.controls.title')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('audit.controls.subtitle')}</p>
        </div>
        {!showForm && (
          <button
            onClick={() => { setShowForm(true); setEditingId(null); setForm(emptyForm); }}
            className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {t('audit.controls.create')}
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5 flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {editingId ? t('audit.controls.edit') : t('audit.controls.create')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('audit.controls.code')} *</label>
              <input
                type="text" value={form.code} disabled={!!editingId}
                onChange={(e) => setForm({ ...form, code: e.target.value })}
                required maxLength={50}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('audit.controls.name_label')} *</label>
              <input
                type="text" value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required maxLength={200}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('audit.controls.framework')} *</label>
              <input
                type="text" value={form.framework} disabled={!!editingId}
                onChange={(e) => setForm({ ...form, framework: e.target.value })}
                required maxLength={50}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('audit.controls.description')}</label>
              <input
                type="text" value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                maxLength={500}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={createMutation.isPending || updateMutation.isPending}
              className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
              {(createMutation.isPending || updateMutation.isPending) ? t('common.saving') : t('common.save')}
            </button>
            <button type="button" onClick={resetForm}
              className="inline-flex items-center rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
              {t('common.cancel')}
            </button>
          </div>
        </form>
      )}

      {isLoading && <Loading />}
      {isError && <ErrorState message={(error as Error)?.message || t('common.error')} onRetry={refetch} />}
      {data && data.length === 0 && <EmptyState message={t('audit.controls.no_controls')} />}

      {data && data.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.controls.code')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.controls.name_label')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.controls.framework')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('audit.controls.type')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.status')}</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {data.map((control) => (
                <tr key={control.id} className={!control.is_active ? 'opacity-50' : ''}>
                  <td className="px-4 py-3 text-sm font-mono font-medium text-gray-900 dark:text-white">{control.code}</td>
                  <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{control.name}</td>
                  <td className="px-4 py-3 text-sm">
                    <Badge variant="info">{control.framework}</Badge>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {control.is_predefined ? (
                      <Badge variant="default">
                        <svg viewBox="0 0 24 24" className="h-3 w-3 mr-1" fill="none" stroke="currentColor" strokeWidth="1.5">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                        </svg>
                        {t('audit.controls.predefined')}
                      </Badge>
                    ) : (
                      <Badge variant="purple">{t('audit.controls.custom')}</Badge>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Badge variant={control.is_active ? 'success' : 'default'}>
                      {control.is_active ? t('audit.controls.active') : t('audit.controls.inactive')}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-right">
                    {control.is_active && !control.is_predefined && (
                      <div className="flex gap-2 justify-end">
                        <button onClick={() => startEdit(control)} className="text-blue-600 dark:text-blue-400 hover:underline text-xs">
                          {t('common.edit')}
                        </button>
                        <button
                          onClick={() => { if (confirm(t('audit.controls.confirm_deactivate'))) deactivateMutation.mutate(control.id); }}
                          className="text-red-600 dark:text-red-400 hover:underline text-xs"
                        >
                          {t('audit.controls.deactivate')}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
