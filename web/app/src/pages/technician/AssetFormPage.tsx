import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { CustomFieldsForm } from '../../components/custom-fields/CustomFieldsForm';
import { useI18n } from '../../lib/i18n';
import type { AssetTypeDefinition } from '../../types';

export default function AssetFormPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { data: assetTypes } = useQuery({
    queryKey: ['asset-types-active'],
    queryFn: async () => {
      const { data } = await api.get('/asset-types', { params: { active_only: true } });
      return data.data as AssetTypeDefinition[];
    },
  });

  const [form, setForm] = useState({
    type: '', brand: '', model: '', serial_number: '',
    purchase_date: '', warranty_expiration: '', notes: '',
  });
  const [error, setError] = useState('');
  const [customFieldsData, setCustomFieldsData] = useState<Record<string, unknown>>({});

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = { ...form };
      if (!payload.type) payload.type = assetTypes?.[0]?.code ?? '';
      if (!payload.purchase_date) delete (payload as Record<string, unknown>).purchase_date;
      if (!payload.warranty_expiration) delete (payload as Record<string, unknown>).warranty_expiration;
      if (!payload.notes) delete (payload as Record<string, unknown>).notes;
      (payload as Record<string, unknown>).custom_fields_data = Object.keys(customFieldsData).length ? customFieldsData : undefined;
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
    <div className="mx-auto max-w-4xl">
      <div className="mb-5">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.asset_form.title')}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t('page.asset_form.subtitle')}</p>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-5">
        <Card className="overflow-hidden p-0">
          <div className="border-b border-border px-5 py-3.5">
            <h3 className="text-sm font-medium text-foreground">{t('page.asset_form.asset_info')}</h3>
          </div>
          <div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-2">
            {error && (
              <div className="rounded-md border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive md:col-span-2">
                {error}
              </div>
            )}

            <div className="md:col-span-2">
              <label className="mb-1.5 block text-sm text-muted-foreground">{t('table.type')}</label>
              <select value={form.type || (assetTypes?.[0]?.code ?? '')} onChange={(e) => set('type', e.target.value)} className="w-full bg-card">
                {(assetTypes ?? []).map((at) => (
                  <option key={at.code} value={at.code}>{at.name}</option>
                ))}
              </select>
            </div>

            {['brand', 'model', 'serial_number'].map((field) => (
              <div key={field}>
                <label className="mb-1.5 block text-sm text-muted-foreground">{t(`table.${field}`)}</label>
                <input value={form[field as keyof typeof form]} onChange={(e) => set(field, e.target.value)} required className="w-full bg-card" />
              </div>
            ))}

            <div>
              <label className="mb-1.5 block text-sm text-muted-foreground">{t('table.purchase_date')}</label>
              <input type="date" value={form.purchase_date} onChange={(e) => set('purchase_date', e.target.value)} className="w-full bg-card" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm text-muted-foreground">{t('table.warranty_expiration')}</label>
              <input type="date" value={form.warranty_expiration} onChange={(e) => set('warranty_expiration', e.target.value)} className="w-full bg-card" />
            </div>
          </div>
        </Card>

        <Card className="overflow-hidden p-0">
          <div className="border-b border-border px-5 py-3.5">
            <h3 className="text-sm font-medium text-foreground">{t('page.asset_form.additional_info')}</h3>
          </div>
          <div className="p-5">
            <label className="mb-1.5 block text-sm text-muted-foreground">{t('table.notes')}</label>
            <textarea value={form.notes} onChange={(e) => set('notes', e.target.value)} rows={4} className="w-full resize-none bg-card" />
          </div>
        </Card>

        <CustomFieldsForm
          entityType="asset"
          values={customFieldsData}
          onChange={setCustomFieldsData}
        />

        <div className="flex items-center justify-end gap-3">
          <button type="button" onClick={() => navigate(-1)} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50">
            {t('common.cancel')}
          </button>
          <button type="submit" disabled={mutation.isPending} className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50">
            {mutation.isPending ? t('page.asset_form.creating') : t('page.asset_form.create')}
          </button>
        </div>
      </form>
    </div>
  );
}
