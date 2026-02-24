import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { EmptyState, ErrorState } from '../../components/ui/StateBlock';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../components/ui/Toast';

interface SlaPolicy {
  id: string;
  name: string;
  priority: string;
  request_type: string | null;
  response_time_hours: number;
  resolution_time_hours: number;
  warning_threshold_pct: number;
  escalate_on_breach: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface PolicyForm {
  name: string;
  priority: string;
  request_type: string;
  response_time_hours: string;
  resolution_time_hours: string;
  warning_threshold_pct: string;
  escalate_on_breach: boolean;
}

const emptyForm: PolicyForm = {
  name: '',
  priority: 'high',
  request_type: '',
  response_time_hours: '',
  resolution_time_hours: '',
  warning_threshold_pct: '75',
  escalate_on_breach: false,
};

const PRIORITIES = ['urgent', 'high', 'medium', 'low'];
const REQUEST_TYPES = ['incident', 'new_equipment', 'onboarding', 'repair', 'configuration', 'access_request'];

export default function SlaPoliciesPage() {
  const { t } = useI18n();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<PolicyForm>(emptyForm);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['sla-policies'],
    queryFn: async () => {
      const { data } = await api.get('/sla/policies');
      return data.data as SlaPolicy[];
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, unknown> = {
        name: form.name,
        priority: form.priority,
        response_time_hours: parseFloat(form.response_time_hours),
        resolution_time_hours: parseFloat(form.resolution_time_hours),
        warning_threshold_pct: parseInt(form.warning_threshold_pct),
        escalate_on_breach: form.escalate_on_breach,
      };
      if (form.request_type) body.request_type = form.request_type;
      await api.post('/sla/policies', body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sla-policies'] });
      toast.success(t('page.sla.policy_created'));
      resetForm();
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      toast.error(message);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, unknown> = {
        name: form.name,
        response_time_hours: parseFloat(form.response_time_hours),
        resolution_time_hours: parseFloat(form.resolution_time_hours),
        warning_threshold_pct: parseInt(form.warning_threshold_pct),
        escalate_on_breach: form.escalate_on_breach,
      };
      await api.put(`/sla/policies/${editingId}`, body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sla-policies'] });
      toast.success(t('page.sla.policy_updated'));
      resetForm();
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('common.error');
      toast.error(message);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/sla/policies/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sla-policies'] });
      toast.success(t('page.sla.policy_deactivated'));
    },
  });

  const resetForm = () => {
    setShowForm(false);
    setEditingId(null);
    setForm(emptyForm);
  };

  const startEdit = (policy: SlaPolicy) => {
    setEditingId(policy.id);
    setForm({
      name: policy.name,
      priority: policy.priority,
      request_type: policy.request_type || '',
      response_time_hours: String(policy.response_time_hours),
      resolution_time_hours: String(policy.resolution_time_hours),
      warning_threshold_pct: String(policy.warning_threshold_pct),
      escalate_on_breach: policy.escalate_on_breach,
    });
    setShowForm(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim() || !form.response_time_hours || !form.resolution_time_hours) return;
    if (editingId) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };

  const formatHours = (hours: number) => {
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    if (hours >= 24 && hours % 24 === 0) return `${hours / 24}d`;
    return `${hours}h`;
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('page.sla.title')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t('page.sla.subtitle')}</p>
        </div>
        {!showForm && (
          <button
            onClick={() => { setShowForm(true); setEditingId(null); setForm(emptyForm); }}
            className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {t('page.sla.create_policy')}
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-5 flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {editingId ? t('page.sla.edit_policy') : t('page.sla.create_policy')}
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('page.sla.policy_name')} *</label>
              <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required maxLength={100}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('page.sla.priority')} *</label>
              <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })} disabled={!!editingId}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm">
                {PRIORITIES.map((p) => <option key={p} value={p}>{t(`page.sla.priority_${p}`)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('page.sla.request_type')}</label>
              <select value={form.request_type} onChange={(e) => setForm({ ...form, request_type: e.target.value })} disabled={!!editingId}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm">
                <option value="">{t('page.sla.all_types')}</option>
                {REQUEST_TYPES.map((rt) => <option key={rt} value={rt}>{rt.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('page.sla.warning_threshold')}</label>
              <input type="number" value={form.warning_threshold_pct} onChange={(e) => setForm({ ...form, warning_threshold_pct: e.target.value })}
                min={1} max={99}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('page.sla.response_time')} *</label>
              <input type="number" value={form.response_time_hours} onChange={(e) => setForm({ ...form, response_time_hours: e.target.value })}
                min={0.1} step="any" required
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('page.sla.resolution_time')} *</label>
              <input type="number" value={form.resolution_time_hours} onChange={(e) => setForm({ ...form, resolution_time_hours: e.target.value })}
                min={0.1} step="any" required
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm" />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input type="checkbox" checked={form.escalate_on_breach} onChange={(e) => setForm({ ...form, escalate_on_breach: e.target.checked })}
              className="rounded border-gray-300" />
            {t('page.sla.escalate_on_breach')}
          </label>

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
      {data && data.length === 0 && <EmptyState title={t('page.sla.no_policies')} />}

      {data && data.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('page.sla.policy_name')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('page.sla.priority')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('page.sla.request_type')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('page.sla.response_time')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('page.sla.resolution_time')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.status')}</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {data.map((policy) => (
                <tr key={policy.id} className={!policy.is_active ? 'opacity-50' : ''}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{policy.name}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      policy.priority === 'urgent' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                      policy.priority === 'high' ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' :
                      policy.priority === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                      'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    }`}>
                      {t(`page.sla.priority_${policy.priority}`)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {policy.request_type ? policy.request_type.replace(/_/g, ' ') : t('page.sla.all_types')}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{formatHours(policy.response_time_hours)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{formatHours(policy.resolution_time_hours)}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      policy.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {policy.is_active ? t('page.sla.active') : t('page.sla.inactive')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-right">
                    {policy.is_active && (
                      <div className="flex gap-2 justify-end">
                        <button onClick={() => startEdit(policy)} className="text-blue-600 dark:text-blue-400 hover:underline text-xs">
                          {t('common.edit')}
                        </button>
                        <button
                          onClick={() => { if (confirm(t('page.sla.confirm_deactivate'))) deactivateMutation.mutate(policy.id); }}
                          className="text-red-600 dark:text-red-400 hover:underline text-xs"
                        >
                          {t('page.sla.deactivate')}
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
