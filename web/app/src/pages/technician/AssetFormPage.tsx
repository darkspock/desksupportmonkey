import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { useI18n } from '../../lib/i18n';

export default function AssetFormPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    type: 'laptop', brand: '', model: '', serial_number: '',
    purchase_date: '', warranty_expiration: '', notes: '',
  });
  const [error, setError] = useState('');

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = { ...form };
      if (!payload.purchase_date) delete (payload as Record<string, unknown>).purchase_date;
      if (!payload.warranty_expiration) delete (payload as Record<string, unknown>).warranty_expiration;
      if (!payload.notes) delete (payload as Record<string, unknown>).notes;
      const { data } = await api.post('/assets', payload);
      return data.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      navigate(`/assets/${data.id}`);
    },
    onError: (err: unknown) => {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.asset_form.error_create'));
    },
  });

  const set = (k: string, v: string) => setForm({ ...form, [k]: v });

  return (
    <div className="max-w-xl">
      <h2 className="text-xl font-bold text-gray-900 mb-4">{t('page.asset_form.title')}</h2>
      <Card>
        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('table.type')}</label>
            <select value={form.type} onChange={(e) => set('type', e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
              {['laptop', 'desktop', 'phone', 'tablet', 'monitor', 'printer', 'other'].map((assetType) => (
                <option key={assetType} value={assetType}>{t(`enum.${assetType}`)}</option>
              ))}
            </select>
          </div>
          {['brand', 'model', 'serial_number'].map((field) => (
            <div key={field}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t(`table.${field}`)}</label>
              <input value={form[field as keyof typeof form]} onChange={(e) => set(field, e.target.value)} required className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          ))}
          {['purchase_date', 'warranty_expiration'].map((field) => (
            <div key={field}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t(`table.${field}`)}</label>
              <input type="date" value={form[field as keyof typeof form]} onChange={(e) => set(field, e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
          ))}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('table.notes')}</label>
            <textarea value={form.notes} onChange={(e) => set('notes', e.target.value)} rows={3} className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={mutation.isPending} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
              {mutation.isPending ? t('page.asset_form.creating') : t('page.asset_form.create')}
            </button>
            <button type="button" onClick={() => navigate(-1)} className="px-4 py-2 rounded-lg text-sm border hover:bg-gray-50">{t('common.cancel')}</button>
          </div>
        </form>
      </Card>
    </div>
  );
}
