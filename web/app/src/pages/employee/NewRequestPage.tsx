import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';
import { CustomFieldsForm } from '../../components/custom-fields/CustomFieldsForm';
import { useAuth } from '../../contexts/AuthContext';
import type { RequestType } from '../../types';
import { VALID_SUBTYPES } from '../../types';

// Map request subtypes to equipment profile asset types
const SUBTYPE_ASSET_MAP: Record<string, string[]> = {
  computer: ['laptop'],
  mobile: [],
  peripheral: ['keyboard', 'mouse', 'headset', 'docking_station'],
  monitor: ['monitor'],
  software_license: [],
};

const TYPE_CONFIG: { key: RequestType; icon: React.ReactNode; descKey: string }[] = [
  {
    key: 'incident',
    descKey: 'page.new_request.type_desc_incident',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 8v4M12 16h.01" />
      </svg>
    ),
  },
  {
    key: 'new_equipment',
    descKey: 'page.new_request.type_desc_new_equipment',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 17v4" />
      </svg>
    ),
  },
  {
    key: 'onboarding',
    descKey: 'page.new_request.type_desc_onboarding',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M19 8v6M22 11h-6" />
      </svg>
    ),
  },
  {
    key: 'repair',
    descKey: 'page.new_request.type_desc_repair',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76Z" />
      </svg>
    ),
  },
  {
    key: 'configuration',
    descKey: 'page.new_request.type_desc_configuration',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  {
    key: 'access_request',
    descKey: 'page.new_request.type_desc_access_request',
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
        <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </svg>
    ),
  },
];

export default function NewRequestPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { isRole } = useAuth();
  const [searchParams] = useSearchParams();
  const onBehalfOf = searchParams.get('on_behalf_of');
  const onBehalfOfLabel = searchParams.get('on_behalf_of_label');
  const [form, setForm] = useState<{ type: RequestType; title: string; description: string; subtype: string }>({
    type: '' as RequestType,
    title: '',
    description: '',
    subtype: '',
  });
  const [customFieldsData, setCustomFieldsData] = useState<Record<string, unknown>>({});

  const subtypeOptions = form.type ? (VALID_SUBTYPES[form.type] ?? []) : [];

  const budgetQuery = useQuery({
    queryKey: ['my-budget'],
    queryFn: async () => {
      const { data } = await api.get('/equipment-profiles/my-budget');
      return data.data as { items: { asset_type: string; budget_cents: number }[] };
    },
    enabled: form.type === 'new_equipment',
  });

  const matchingBudgets = (() => {
    if (!budgetQuery.data?.items?.length || !form.subtype) return [];
    const assetTypes = SUBTYPE_ASSET_MAP[form.subtype] ?? [];
    if (!assetTypes.length) return [];
    return budgetQuery.data.items.filter((b) => assetTypes.includes(b.asset_type));
  })();

  const showError = (msg: string) => {
    showToast({ title: msg, variant: 'error', durationMs: 5000 });
  };

  const mutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, unknown> = {
        type: form.type,
        title: form.title,
        description: form.description,
      };
      if (form.subtype) body.subtype = form.subtype;
      if (onBehalfOf) body.on_behalf_of = onBehalfOf;
      if (Object.keys(customFieldsData).length) body.custom_fields_data = customFieldsData;
      const { data } = await api.post('/requests', body);
      return data.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['my-requests'] });
      navigate(`/requests/${data.id}`);
    },
    onError: (err: unknown) => {
      showError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.new_request.error_create'),
      );
    },
  });

  const handleSubmit = () => {
    if (!form.type) {
      showError(t('page.new_request.error_type_required'));
      return;
    }
    if (!form.title.trim()) {
      showError(t('page.new_request.error_title_required'));
      return;
    }
    if (!form.description.trim()) {
      showError(t('page.new_request.error_description_required'));
      return;
    }
    mutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          {t('page.new_request.title')}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {t('page.new_request.subtitle')}
        </p>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} className="space-y-6">
        <div className="rounded-lg border border-border bg-card p-6 space-y-6">
          {onBehalfOfLabel && (
            <div className="flex items-center gap-2 rounded-md bg-primary/10 px-3 py-2 text-sm text-primary">
              <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
              </svg>
              {t('page.new_request.on_behalf_of')} <span className="font-medium">{onBehalfOfLabel}</span>
            </div>
          )}
          {/* Type selector cards */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-3">{t('page.new_request.type_label')}</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {TYPE_CONFIG.map((cfg) => (
                <button
                  key={cfg.key}
                  type="button"
                  onClick={() => setForm({ ...form, type: cfg.key, subtype: '' })}
                  className={`flex flex-col items-start gap-3 rounded-lg border p-4 text-left transition-all hover:border-primary ${
                    form.type === cfg.key ? 'border-primary bg-primary/5' : 'border-border'
                  }`}
                >
                  <div className={`flex h-10 w-10 items-center justify-center rounded-md ${
                    form.type === cfg.key ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                  }`}>
                    {cfg.icon}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{t(`enum.${cfg.key}`)}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{t(cfg.descKey)}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Title + Subtype row */}
          <div className={`grid grid-cols-1 gap-4 ${subtypeOptions.length > 0 ? 'md:grid-cols-2' : ''}`}>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-foreground">{t('table.title')} *</label>
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full"
                placeholder={t('page.new_request.title_placeholder')}
              />
            </div>
            {subtypeOptions.length > 0 && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">{t('page.new_request.subtype')}</label>
                <select
                  value={form.subtype}
                  onChange={(e) => setForm({ ...form, subtype: e.target.value })}
                  className="w-full"
                >
                  <option value="">{t('page.new_request.select_subtype')}</option>
                  {subtypeOptions.map((sub) => (
                    <option key={sub} value={sub}>{t(`enum.${sub}`)}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Budget indicator for new_equipment */}
          {form.type === 'new_equipment' && form.subtype && (
            <div className="flex items-center gap-2 rounded-md border border-border bg-muted/50 px-3 py-2 text-sm">
              <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
              {matchingBudgets.length > 0 ? (
                <span className="text-foreground">
                  {matchingBudgets.map((b) => (
                    <span key={b.asset_type}>
                      {t('page.new_request.budget_amount', { amount: (b.budget_cents / 100).toLocaleString() })}
                      {' '}
                      <span className="text-muted-foreground">({t(`enum.${b.asset_type}`)})</span>
                    </span>
                  ))}
                </span>
              ) : (
                <span className="text-muted-foreground">{t('page.new_request.no_budget_set')}</span>
              )}
            </div>
          )}

          {/* Description */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">{t('table.description')} *</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={5}
              className="w-full resize-none"
              placeholder={t('page.new_request.description_placeholder')}
            />
            <p className="text-xs text-muted-foreground">
              {t('page.new_request.description_hint')}
            </p>
          </div>

          {/* Custom Fields */}
          <CustomFieldsForm
            entityType="request"
            values={customFieldsData}
            onChange={setCustomFieldsData}
            isEmployee={isRole('employee')}
          />
        </div>

        {/* Buttons — right-aligned */}
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground transition-all disabled:opacity-50"
          >
            {t('common.cancel')}
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {mutation.isPending ? t('page.new_request.submitting') : t('page.new_request.submit')}
          </button>
        </div>
      </form>
    </div>
  );
}
