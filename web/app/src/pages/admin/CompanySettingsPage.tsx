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
    <div className="max-w-3xl">
      <h2 className="mb-1 text-xl font-bold text-gray-900">{t('page.company_settings.title')}</h2>
      <p className="mb-4 text-sm text-gray-600">{t('page.company_settings.subtitle')}</p>

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
              <label className="mb-1 block text-sm font-medium text-gray-700">{t('auth.register.company_name')}</label>
              <input
                value={data?.name ?? ''}
                readOnly
                className="h-10 w-full rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm text-gray-700"
              />
            </div>

            <div>
              <label htmlFor="company-domains" className="mb-1 block text-sm font-medium text-gray-700">{t('auth.register.allowed_domains')}</label>
              <input
                id="company-domains"
                value={currentDomainsInput}
                onChange={(e) => {
                  setDomainsInput(e.target.value);
                  setIsDirty(true);
                }}
                placeholder={t('common.placeholder_domains')}
                className="h-10 w-full rounded-lg border border-gray-300 px-3 text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">{t('page.company_settings.domains_help')}</p>
            </div>

            {normalizedDomains.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {normalizedDomains.map((domain) => (
                  <span key={domain} className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs font-medium text-gray-700">
                    {domain}
                  </span>
                ))}
              </div>
            )}

            <button
              type="submit"
              disabled={saveSettings.isPending || !isDirty}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saveSettings.isPending ? t('page.company_settings.saving') : t('page.company_settings.save')}
            </button>
          </form>
        )}
      </Card>
    </div>
  );
}
