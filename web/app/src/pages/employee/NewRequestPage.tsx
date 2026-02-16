import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { useI18n } from '../../lib/i18n';

export default function NewRequestPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ type: 'incident', title: '', description: '' });
  const [error, setError] = useState('');

  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/requests', form);
      return data.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['my-requests'] });
      navigate(`/requests/${data.id}`);
    },
    onError: (err: unknown) => {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.new_request.error_create'));
    },
  });

  return (
    <div className="max-w-xl">
      <h2 className="text-xl font-bold text-gray-900 mb-4">{t('page.new_request.title')}</h2>
      <Card>
        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          {error && <p className="text-sm text-red-600">{error}</p>}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('table.type')}</label>
            <select
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            >
              <option value="incident">{t('enum.incident')}</option>
              <option value="new_equipment">{t('enum.new_equipment')}</option>
              <option value="onboarding">{t('enum.onboarding')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('table.title')}</label>
            <input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              required
              className="w-full border rounded-lg px-3 py-2 text-sm"
              placeholder={t('page.new_request.title_placeholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('table.description')}</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              required
              rows={4}
              className="w-full border rounded-lg px-3 py-2 text-sm"
              placeholder={t('page.new_request.description_placeholder')}
            />
          </div>

          <div className="flex gap-3">
            <button type="submit" disabled={mutation.isPending} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
              {mutation.isPending ? t('page.new_request.submitting') : t('page.new_request.submit')}
            </button>
            <button type="button" onClick={() => navigate(-1)} className="px-4 py-2 rounded-lg text-sm border hover:bg-gray-50">
              {t('common.cancel')}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
}
