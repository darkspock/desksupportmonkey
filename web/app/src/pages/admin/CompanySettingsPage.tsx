import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import { SECTORS } from '../../config/moduleConfig';
import type { CompanySettings } from '../../types';

export default function CompanySettingsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [domainsInput, setDomainsInput] = useState('');
  const [sectorValue, setSectorValue] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);
  const [sectorDirty, setSectorDirty] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['my-company-settings'],
    queryFn: async () => {
      const { data } = await api.get('/my/company-settings');
      return data.data as CompanySettings;
    },
  });

  const currentDomainsInput = isDirty ? domainsInput : (data?.email_domains.join(', ') ?? '');
  const currentSector = sectorDirty ? sectorValue : (data?.sector ?? null);

  const normalizedDomains = useMemo(
    () => Array.from(new Set(
      currentDomainsInput
        .split(',')
        .map((d) => d.trim().toLowerCase())
        .filter(Boolean),
    )),
    [currentDomainsInput],
  );

  const saveSettings = useMutation({
    mutationFn: (payload: { email_domains: string[]; sector?: string | null }) =>
      api.put('/my/company-settings', payload),
    onSuccess: (res) => {
      const next = res.data.data as CompanySettings;
      queryClient.setQueryData(['my-company-settings'], next);
      setDomainsInput(next.email_domains.join(', '));
      setIsDirty(false);
      setSectorDirty(false);
      showToast({ title: t('page.company_settings.toast_updated'), variant: 'success' });
      if (sectorDirty) {
        showToast({ title: t('company_settings.sector_changed_hint'), variant: 'info' });
      }
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.company_settings.error_update');
      showToast({ title: t('page.company_settings.error_update_title'), description: detail, variant: 'error' });
    },
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (normalizedDomains.length === 0) {
      showToast({ title: t('page.company_settings.error_domains_required'), variant: 'error' });
      return;
    }

    const payload: { email_domains: string[]; sector?: string | null } = {
      email_domains: normalizedDomains,
    };
    if (sectorDirty) {
      payload.sector = currentSector || null;
    }
    saveSettings.mutate(payload);
  };

  const anyDirty = isDirty || sectorDirty;

  return (
    <div className="mx-auto max-w-3xl">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.company_settings.title')}</h2>
      <p className="mt-1 text-sm text-muted-foreground mb-4">{t('page.company_settings.subtitle')}</p>

      <Card>
        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.company_settings.error_load')}
            onRetry={() => {
              void refetch();
            }}
          />
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block mb-1.5 text-muted-foreground">{t('auth.register.company_name')}</label>
              <input
                value={data?.name ?? ''}
                readOnly
                className="w-full bg-secondary"
              />
            </div>

            <div>
              <label htmlFor="company-sector" className="block mb-1.5 text-muted-foreground">{t('company_settings.sector')}</label>
              <select
                id="company-sector"
                value={currentSector ?? ''}
                onChange={(e) => {
                  setSectorValue(e.target.value || null);
                  setSectorDirty(true);
                }}
                className="w-full bg-card rounded-md border border-border px-3 py-2 text-sm"
              >
                <option value="">{t('company_settings.sector_placeholder')}</option>
                {SECTORS.map((s) => (
                  <option key={s.id} value={s.id}>{t(s.labelKey)}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="company-domains" className="block mb-1.5 text-muted-foreground">{t('auth.register.allowed_domains')}</label>
              <input
                id="company-domains"
                value={currentDomainsInput}
                onChange={(e) => {
                  setDomainsInput(e.target.value);
                  setIsDirty(true);
                }}
                placeholder={t('common.placeholder_domains')}
                className="w-full bg-card"
              />
              <p className="mt-1 text-xs text-muted-foreground">{t('page.company_settings.domains_help')}</p>
            </div>

            {normalizedDomains.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {normalizedDomains.map((domain) => (
                  <span key={domain} className="rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-foreground">
                    {domain}
                  </span>
                ))}
              </div>
            )}

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={saveSettings.isPending || !anyDirty}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
              >
                {saveSettings.isPending ? t('page.company_settings.saving') : t('page.company_settings.save')}
              </button>

              <button
                type="button"
                onClick={() => navigate('/onboarding?rerun=true')}
                className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium border border-border bg-card text-foreground shadow-xs transition-all hover:bg-secondary"
              >
                {t('company_settings.rerun_wizard')}
              </button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
