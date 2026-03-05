import { useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthShell } from '../../components/auth/AuthShell';
import { useI18n } from '../../lib/i18n';
import api from '../../lib/api';

export default function ResellerForgotPasswordPage() {
  const { t } = useI18n();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/reseller/auth/forgot-password', { email });
    } catch {
      // Silent — no email enumeration
    } finally {
      setLoading(false);
      setSubmitted(true);
    }
  };

  return (
    <AuthShell title={t('reseller.forgot_password.title')} subtitle={t('reseller.forgot_password.subtitle')} showBackToLogin={false}>
      {submitted ? (
        <div className="space-y-4 text-center">
          <div className="rounded-lg border border-green-200 bg-green-50 p-4">
            <p className="text-sm text-green-800">{t('reseller.forgot_password.success')}</p>
          </div>
          <Link to="/reseller/login" className="text-sm font-medium text-primary hover:underline">
            {t('reseller.register.login_link')}
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="fp-email" className="block mb-1.5 text-sm text-muted-foreground">
              {t('reseller.forgot_password.email')}
            </label>
            <input
              id="fp-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full"
              placeholder="you@company.com"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? t('common.working') : t('reseller.forgot_password.submit')}
          </button>

          <p className="text-center text-sm text-muted-foreground">
            <Link to="/reseller/login" className="font-medium text-primary hover:underline">
              {t('reseller.register.login_link')}
            </Link>
          </p>
        </form>
      )}
    </AuthShell>
  );
}
