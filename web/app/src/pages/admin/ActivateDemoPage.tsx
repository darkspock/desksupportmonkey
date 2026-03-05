import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useI18n } from '../../lib/i18n';
import { useToast } from '../../hooks/useToast';
import { Card } from '../../components/ui/Card';
import api from '../../lib/api';

export default function ActivateDemoPage() {
  const { user, refreshUser } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const companyName = user?.company_name?.replace(/\s*\(Demo\)\s*$/i, '') ?? '';

  const [name, setName] = useState(companyName);
  const [domains, setDomains] = useState('');
  const [keepData, setKeepData] = useState(true);
  const [termsAccepted, setTermsAccepted] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      const emailDomains = domains
        .split(/[,\s]+/)
        .map((d) => d.trim())
        .filter(Boolean);
      await api.post('/my/activate-demo', {
        company_name: name.trim(),
        email_domains: emailDomains,
        keep_demo_data: keepData,
      });
    },
    onSuccess: async () => {
      showToast({ title: t('demo.activate.success'), variant: 'success' });
      await refreshUser();
      navigate('/billing');
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail ?? t('common.error');
      showToast({ title: detail, variant: 'error' });
    },
  });

  if (user?.company_plan !== 'demo') {
    navigate('/billing');
    return null;
  }

  const canSubmit = name.trim() && domains.trim() && termsAccepted && !mutation.isPending;

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">{t('demo.activate.title')}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t('demo.activate.subtitle')}</p>
      </div>

      <Card>
        <form
          className="space-y-5"
          onSubmit={(e) => {
            e.preventDefault();
            if (canSubmit) mutation.mutate();
          }}
        >
          {/* Company name */}
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-foreground">
              {t('demo.activate.company_name')}
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={200}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder={t('common.placeholder_company_name')}
            />
          </div>

          {/* Email domains */}
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-foreground">
              {t('demo.activate.email_domains')}
            </label>
            <input
              type="text"
              value={domains}
              onChange={(e) => setDomains(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder={t('common.placeholder_domains')}
            />
            <p className="text-xs text-muted-foreground">
              {t('demo.activate.domains_hint')}
            </p>
          </div>

          {/* Keep demo data toggle */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              role="switch"
              aria-checked={keepData}
              onClick={() => setKeepData(!keepData)}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                keepData ? 'bg-primary' : 'bg-muted'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition-transform ${
                  keepData ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
            <label className="text-sm text-foreground">
              {t('demo.activate.keep_data')}
            </label>
          </div>

          {/* Terms checkbox */}
          <label className="flex items-start gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300"
            />
            <span>{t('demo.activate.terms')}</span>
          </label>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2 border-t border-border">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-all"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium shadow-xs bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all"
            >
              {mutation.isPending ? t('common.working') : t('demo.activate.submit')}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
}
