import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../lib/api';
import { Loading } from '../../components/ui/Loading';
import { Card } from '../../components/ui/Card';
import { ErrorState } from '../../components/ui/StateBlock';
import { useToast } from '../../hooks/useToast';
import { useI18n } from '../../lib/i18n';
import type { CompanyAIConfig } from '../../types';

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'groq', label: 'Groq' },
];

export default function AssignmentAISettingsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [provider, setProvider] = useState('openai');
  const [promptTemplate, setPromptTemplate] = useState('');
  const [model, setModel] = useState('');
  const [isDirty, setIsDirty] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['assignment-ai-config'],
    queryFn: async () => {
      const { data } = await api.get('/settings/assignment-ai');
      return (data.data ?? null) as CompanyAIConfig | null;
    },
  });

  useEffect(() => {
    if (data && !isDirty) {
      setProvider(data.provider);
      setPromptTemplate(data.prompt_template);
      setModel(data.model ?? '');
    }
  }, [data, isDirty]);

  const save = useMutation({
    mutationFn: () =>
      api.put('/settings/assignment-ai', {
        provider,
        prompt_template: promptTemplate,
        model: model || null,
      }),
    onSuccess: (res) => {
      const next = (res.data.data ?? null) as CompanyAIConfig | null;
      queryClient.setQueryData(['assignment-ai-config'], next);
      setIsDirty(false);
      showToast({ title: t('page.assignment_ai.toast_saved'), variant: 'success' });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.assignment_ai.error_save');
      showToast({ title: t('page.assignment_ai.error_save_title'), description: detail, variant: 'error' });
    },
  });

  function markDirty() {
    if (!isDirty) setIsDirty(true);
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground">{t('page.assignment_ai.title')}</h2>
      <p className="mt-1 text-sm text-muted-foreground mb-4">{t('page.assignment_ai.subtitle')}</p>

      <Card>
        {isLoading ? (
          <Loading />
        ) : isError ? (
          <ErrorState
            message={(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('page.assignment_ai.error_load')}
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
              <label htmlFor="ai-provider" className="block mb-1.5 text-muted-foreground">
                {t('page.assignment_ai.provider')}
              </label>
              <select
                id="ai-provider"
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
              <label htmlFor="ai-prompt" className="block mb-1.5 text-muted-foreground">
                {t('page.assignment_ai.prompt_template')}
              </label>
              <textarea
                id="ai-prompt"
                value={promptTemplate}
                onChange={(e) => { setPromptTemplate(e.target.value); markDirty(); }}
                rows={6}
                required
                className="w-full bg-card"
              />
              <p className="mt-1 text-xs text-muted-foreground">{t('page.assignment_ai.prompt_help')}</p>
            </div>

            <div>
              <label htmlFor="ai-model" className="block mb-1.5 text-muted-foreground">
                {t('page.assignment_ai.model')}
              </label>
              <input
                id="ai-model"
                value={model}
                onChange={(e) => { setModel(e.target.value); markDirty(); }}
                placeholder={t('page.assignment_ai.model_placeholder')}
                className="w-full bg-card"
              />
              <p className="mt-1 text-xs text-muted-foreground">{t('page.assignment_ai.model_help')}</p>
            </div>

            <button
              type="submit"
              disabled={save.isPending || !isDirty || !promptTemplate.trim()}
              className="inline-flex items-center justify-center gap-2 rounded-md h-9 px-4 text-sm font-medium bg-primary text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
            >
              {save.isPending ? t('page.assignment_ai.saving') : t('page.assignment_ai.save')}
            </button>
          </form>
        )}
      </Card>
    </div>
  );
}
