import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { AuthShell } from '../../components/auth/AuthShell';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';
import { getDefaultRouteForRole } from '../../lib/navigation';
import { useI18n } from '../../lib/i18n';

export default function RegisterPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [name, setName] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [emailDomains, setEmailDomains] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to={getDefaultRouteForRole(user.role)} replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const domains = emailDomains
        .split(',')
        .map((d) => d.trim())
        .filter(Boolean);

      if (domains.length === 0) {
        setError(t('auth.register.error_domains_required'));
        setLoading(false);
        return;
      }

      await api.post('/register', {
        name,
        admin_email: adminEmail,
        email_domains: domains,
      });
      setSent(true);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || t('auth.register.error_registration_failed');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title={t('auth.register.title')} subtitle={t('auth.register.subtitle')} showBackToLogin={false}>
      {sent ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-center">
          <p className="text-sm font-medium text-emerald-800">{t('auth.register.success_title')}</p>
          <p className="mt-1 text-sm text-emerald-700">{t('auth.register.success_desc')}</p>
          <Link to="/auth/login" className="mt-4 inline-block text-sm font-medium text-blue-700 hover:underline">
            {t('auth.back_to_login')}
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

          <div>
            <label htmlFor="company-name" className="mb-1 block text-sm font-medium text-slate-700">{t('auth.register.company_name')}</label>
            <input
              id="company-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('common.placeholder_company_name')}
              required
              className="h-11 w-full rounded-xl border border-slate-300 px-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </div>

          <div>
            <label htmlFor="admin-email" className="mb-1 block text-sm font-medium text-slate-700">{t('auth.register.admin_email')}</label>
            <input
              id="admin-email"
              type="email"
              value={adminEmail}
              onChange={(e) => setAdminEmail(e.target.value)}
              placeholder={t('common.placeholder_admin_email')}
              required
              className="h-11 w-full rounded-xl border border-slate-300 px-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </div>

          <div>
            <label htmlFor="domains" className="mb-1 block text-sm font-medium text-slate-700">{t('auth.register.allowed_domains')}</label>
            <input
              id="domains"
              type="text"
              value={emailDomains}
              onChange={(e) => setEmailDomains(e.target.value)}
              placeholder={t('common.placeholder_domains')}
              required
              className="h-11 w-full rounded-xl border border-slate-300 px-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
            <p className="mt-1 text-xs text-slate-500">{t('auth.register.allowed_domains_help')}</p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="h-11 w-full rounded-xl bg-blue-600 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? t('auth.register.registering') : t('auth.register.register_company')}
          </button>

          <p className="text-center text-sm text-slate-600">
            {t('auth.register.already_have_account')}{' '}
            <Link to="/auth/login" className="font-medium text-blue-700 hover:underline">{t('auth.login.sign_in')}</Link>
          </p>
        </form>
      )}
    </AuthShell>
  );
}
