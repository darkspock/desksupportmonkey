import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { CompanySettings } from '../../types';

export default function CompanySettingsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [domainsInput, setDomainsInput] = useState('');
  const [isDirty, setIsDirty] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['my-company-settings'],
    queryFn: async () => {
      const { data } = await api.get('/my/company-settings');
      return data.data as CompanySettings;
    },
  });

  const currentDomainsInput = isDirty ? domainsInput : (data?.email_domains.join(', ') ?? '');

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
    mutationFn: (emailDomains: string[]) => api.put('/my/company-settings', { email_domains: emailDomains }),
    onSuccess: (res) => {
      const next = res.data.data as CompanySettings;
      queryClient.setQueryData(['my-company-settings'], next);
      setDomainsInput(next.email_domains.join(', '));
      setIsDirty(false);
      showToast({ title: t('page.company_settings.toast_updated'), variant: 'success' });
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

    saveSettings.mutate(normalizedDomains);
  };

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

            <button
              type="submit"
              disabled={saveSettings.isPending || !isDirty}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {saveSettings.isPending ? t('page.company_settings.saving') : t('page.company_settings.save')}
            </button>
          </form>
        )}
      </Card>
    </div>
  );
}
