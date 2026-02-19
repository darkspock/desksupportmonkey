import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { CompanyProcurementConfig } from '../../types';

const ENFORCEMENT_MODES = [
  { value: 'warn', labelKey: 'page.procurement_settings.mode_warn' },
  { value: 'strict', labelKey: 'page.procurement_settings.mode_strict' },
];

const MONTHS = [
  { value: 1, labelKey: 'page.procurement_settings.month_jan' },
  { value: 2, labelKey: 'page.procurement_settings.month_feb' },
  { value: 3, labelKey: 'page.procurement_settings.month_mar' },
  { value: 4, labelKey: 'page.procurement_settings.month_apr' },
  { value: 5, labelKey: 'page.procurement_settings.month_may' },
  { value: 6, labelKey: 'page.procurement_settings.month_jun' },
  { value: 7, labelKey: 'page.procurement_settings.month_jul' },
  { value: 8, labelKey: 'page.procurement_settings.month_aug' },
  { value: 9, labelKey: 'page.procurement_settings.month_sep' },
  { value: 10, labelKey: 'page.procurement_settings.month_oct' },
  { value: 11, labelKey: 'page.procurement_settings.month_nov' },
  { value: 12, labelKey: 'page.procurement_settings.month_dec' },
];

export default function ProcurementSettingsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [enforcementMode, setEnforcementMode] = useState('warn');
  const [thresholdDisplay, setThresholdDisplay] = useState('0');
  const [poPrefix, setPoPrefix] = useState('PO');
  const [fiscalMonth, setFiscalMonth] = useState(1);
  const [currency, setCurrency] = useState('USD');
  const [autoCreateAssets, setAutoCreateAssets] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['procurement-config'],
    queryFn: async () => {
      const { data } = await api.get('/settings/procurement');
      return data.data as CompanyProcurementConfig;
    },
  });

  useEffect(() => {
    if (data && !isDirty) {
      setEnforcementMode(data.enforcement_mode);
      setThresholdDisplay(String(data.approval_threshold_cents / 100));
      setPoPrefix(data.po_number_prefix);
      setFiscalMonth(data.fiscal_year_start_month);
      setCurrency(data.currency);
      setAutoCreateAssets(data.auto_create_assets);
    }
  }, [data, isDirty]);

  const save = useMutation({
    mutationFn: () =>
      api.put('/settings/procurement', {
        enforcement_mode: enforcementMode,
        approval_threshold_cents: Math.round(parseFloat(thresholdDisplay || '0') * 100),
        po_number_prefix: poPrefix,
        fiscal_year_start_month: fiscalMonth,
        currency: currency.toUpperCase(),
        auto_create_assets: autoCreateAssets,
      }),
    onSuccess: (res) => {
      const next = res.data.data as CompanyProcurementConfig;
      queryClient.setQueryData(['procurement-config'], next);
      setIsDirty(false);
      showToast({ title: t('page.procurement_settings.toast_saved'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.procurement_settings.error_save');
      showToast({ title: t('page.procurement_settings.error_save_title'), description: detail, variant: 'error' });
    },
  });

  function markDirty() {
    if (!isDirty) setIsDirty(true);
  }

  const isValid =
    poPrefix.trim().length > 0 &&
    poPrefix.trim().length <= 10 &&
    currency.trim().length === 3 &&
    !isNaN(parseFloat(thresholdDisplay)) &&
    parseFloat(thresholdDisplay) >= 0;

  return (
    <div className="mx-auto max-w-3xl">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.procurement_settings.title')}</h2>
      <p className="mt-1 text-sm text-muted-foreground mb-4">{t('page.procurement_settings.subtitle')}</p>

      <Card>
        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.procurement_settings.error_load')}
            onRetry={() => { void refetch(); }}
          />
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              save.mutate();
            }}
            className="space-y-4"
          >
            <div>
              <label htmlFor="enforcement-mode" className="block mb-1.5 text-muted-foreground">
                {t('page.procurement_settings.enforcement_mode')}
              </label>
              <select
                id="enforcement-mode"
                value={enforcementMode}
                onChange={(e) => { setEnforcementMode(e.target.value); markDirty(); }}
                className="w-full bg-card"
              >
                {ENFORCEMENT_MODES.map((m) => (
                  <option key={m.value} value={m.value}>{t(m.labelKey)}</option>
                ))}
              </select>
              <p className="mt-1 text-xs text-muted-foreground">{t('page.procurement_settings.enforcement_help')}</p>
            </div>

            <div>
              <label htmlFor="threshold" className="block mb-1.5 text-muted-foreground">
                {t('page.procurement_settings.threshold')}
              </label>
              <input
                id="threshold"
                type="number"
                min="0"
                step="0.01"
                value={thresholdDisplay}
                onChange={(e) => { setThresholdDisplay(e.target.value); markDirty(); }}
                className="w-full bg-card"
              />
              <p className="mt-1 text-xs text-muted-foreground">{t('page.procurement_settings.threshold_help')}</p>
            </div>

            <div>
              <label htmlFor="po-prefix" className="block mb-1.5 text-muted-foreground">
                {t('page.procurement_settings.po_prefix')}
              </label>
              <input
                id="po-prefix"
                value={poPrefix}
                onChange={(e) => { setPoPrefix(e.target.value); markDirty(); }}
                maxLength={10}
                className="w-full bg-card"
              />
            </div>

            <div>
              <label htmlFor="fiscal-month" className="block mb-1.5 text-muted-foreground">
                {t('page.procurement_settings.fiscal_month')}
              </label>
              <select
                id="fiscal-month"
                value={fiscalMonth}
                onChange={(e) => { setFiscalMonth(Number(e.target.value)); markDirty(); }}
                className="w-full bg-card"
              >
                {MONTHS.map((m) => (
                  <option key={m.value} value={m.value}>{t(m.labelKey)}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="currency" className="block mb-1.5 text-muted-foreground">
                {t('page.procurement_settings.currency')}
              </label>
              <input
                id="currency"
                value={currency}
                onChange={(e) => { setCurrency(e.target.value); markDirty(); }}
                maxLength={3}
                placeholder="USD"
                className="w-full bg-card"
              />
              <p className="mt-1 text-xs text-muted-foreground">{t('page.procurement_settings.currency_help')}</p>
            </div>

            <div className="flex items-center gap-3">
              <input
                id="auto-create"
                type="checkbox"
                checked={autoCreateAssets}
                onChange={(e) => { setAutoCreateAssets(e.target.checked); markDirty(); }}
                className="h-4 w-4 rounded border-input text-primary"
              />
              <label htmlFor="auto-create" className="text-muted-foreground">
                {t('page.procurement_settings.auto_create')}
              </label>
            </div>

            <button
              type="submit"
              disabled={save.isPending || !isDirty || !isValid}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {save.isPending ? t('page.procurement_settings.saving') : t('page.procurement_settings.save')}
            </button>
          </form>
        )}
      </Card>
    </div>
  );
}
