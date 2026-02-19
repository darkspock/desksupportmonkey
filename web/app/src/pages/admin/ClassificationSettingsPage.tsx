import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { CompanyClassificationConfig } from '../../types';

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'groq', label: 'Groq' },
];

export default function ClassificationSettingsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [isEnabled, setIsEnabled] = useState(false);
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('');
  const [threshold, setThreshold] = useState(0.7);
  const [promptTemplate, setPromptTemplate] = useState('');
  const [timeout, setTimeout] = useState(10);
  const [isDirty, setIsDirty] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['classification-config'],
    queryFn: async () => {
      const { data } = await api.get('/settings/request-classification');
      return (data.data ?? null) as CompanyClassificationConfig | null;
    },
  });

  useEffect(() => {
    if (data && !isDirty) {
      setIsEnabled(data.is_enabled);
      setProvider(data.provider);
      setModel(data.model ?? '');
      setThreshold(data.confidence_threshold);
      setPromptTemplate(data.prompt_template ?? '');
      setTimeout(data.timeout_seconds);
    }
  }, [data, isDirty]);

  const save = useMutation({
    mutationFn: () =>
      api.put('/settings/request-classification', {
        is_enabled: isEnabled,
        provider,
        model: model || null,
        confidence_threshold: threshold,
        prompt_template: promptTemplate || null,
        timeout_seconds: timeout,
      }),
    onSuccess: (res) => {
      const next = (res.data.data ?? null) as CompanyClassificationConfig | null;
      queryClient.setQueryData(['classification-config'], next);
      setIsDirty(false);
      showToast({ title: t('page.classification_settings.toast_saved'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.classification_settings.toast_error');
      showToast({ title: t('page.classification_settings.toast_error'), description: detail, variant: 'error' });
    },
  });

  function markDirty() {
    if (!isDirty) setIsDirty(true);
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.classification_settings.title')}</h2>
      <p className="mt-1 text-sm text-muted-foreground mb-4">{t('page.classification_settings.subtitle')}</p>

      <Card>
        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.classification_settings.error_load')}
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
            <div className="flex items-center gap-3">
              <input
                id="cls-enabled"
                type="checkbox"
                checked={isEnabled}
                onChange={(e) => { setIsEnabled(e.target.checked); markDirty(); }}
                className="h-4 w-4 rounded border-input text-primary"
              />
              <label htmlFor="cls-enabled" className="text-muted-foreground">
                {t('page.classification_settings.enable')}
              </label>
            </div>

            <div>
              <label htmlFor="cls-provider" className="block mb-1.5 text-muted-foreground">
                {t('page.classification_settings.provider')}
              </label>
              <select
                id="cls-provider"
                value={provider}
                onChange={(e) => { setProvider(e.target.value); markDirty(); }}
                className="w-full bg-card"
              >
                {PROVIDERS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="cls-model" className="block mb-1.5 text-muted-foreground">
                {t('page.classification_settings.model')}
              </label>
              <input
                id="cls-model"
                value={model}
                onChange={(e) => { setModel(e.target.value); markDirty(); }}
                placeholder={t('page.classification_settings.model_placeholder')}
                maxLength={100}
                className="w-full bg-card"
              />
            </div>

            <div>
              <label htmlFor="cls-threshold" className="block mb-1.5 text-muted-foreground">
                {t('page.classification_settings.threshold')}
              </label>
              <input
                id="cls-threshold"
                type="number"
                value={threshold}
                onChange={(e) => { setThreshold(parseFloat(e.target.value)); markDirty(); }}
                min={0.5}
                max={1.0}
                step={0.05}
                className="w-full bg-card"
              />
              <p className="mt-1 text-xs text-muted-foreground">{t('page.classification_settings.threshold_help')}</p>
            </div>

            <div>
              <label htmlFor="cls-prompt" className="block mb-1.5 text-muted-foreground">
                {t('page.classification_settings.prompt')}
              </label>
              <textarea
                id="cls-prompt"
                value={promptTemplate}
                onChange={(e) => { setPromptTemplate(e.target.value); markDirty(); }}
                rows={4}
                placeholder={t('page.classification_settings.prompt_placeholder')}
                className="w-full bg-card"
              />
            </div>

            <div>
              <label htmlFor="cls-timeout" className="block mb-1.5 text-muted-foreground">
                {t('page.classification_settings.timeout')}
              </label>
              <input
                id="cls-timeout"
                type="number"
                value={timeout}
                onChange={(e) => { setTimeout(parseInt(e.target.value, 10)); markDirty(); }}
                min={1}
                max={60}
                className="w-full bg-card"
              />
            </div>

            <button
              type="submit"
              disabled={save.isPending || !isDirty}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {save.isPending ? t('common.working') : t('page.classification_settings.save')}
            </button>
          </form>
        )}
      </Card>
    </div>
  );
}
