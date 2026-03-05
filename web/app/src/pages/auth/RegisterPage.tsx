import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { AuthShell } from '../../components/auth/AuthShell';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';
import { getDefaultRouteForRole } from '../../lib/navigation';
import { useI18n } from '../../lib/i18n';
import { getBrandMessages } from '../../config/brand';

const normalizeDomain = (value: string) => value.trim().toLowerCase().replace(/^@+/, '');

export default function RegisterPage() {
  const { user } = useAuth();
  const { t, language } = useI18n();
  const brandMsg = getBrandMessages(language);
  const [name, setName] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [emailDomains, setEmailDomains] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);

  // Set dsm_ref cookie when ref param is present (30-day expiry)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const ref = params.get('ref');
    if (ref) {
      const expires = new Date();
      expires.setDate(expires.getDate() + 30);
      document.cookie = `dsm_ref=${ref}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`;
    }
  }, []);

  if (user) return <Navigate to={getDefaultRouteForRole(user.role)} replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const domains = emailDomains
        .split(',')
        .map(normalizeDomain)
        .filter(Boolean);

      if (domains.length === 0) {
        setError(t('auth.register.error_domains_required'));
        setLoading(false);
        return;
      }

      const invalid = domains.find(
        (d) => d.includes('@') || !d.includes('.') || d.startsWith('.') || d.endsWith('.'),
      );
      if (invalid) {
        setError(t('auth.register.error_invalid_domain', { domain: invalid }));
        setLoading(false);
        return;
      }

      const BLOCKED = ['gmail.com','googlemail.com','yahoo.com','yahoo.es','hotmail.com','hotmail.es','outlook.com','outlook.es','live.com','aol.com','icloud.com','protonmail.com','proton.me','mailinator.com'];
      const blocked = domains.find((d) => BLOCKED.includes(d.toLowerCase()));
      if (blocked) {
        setError(t('auth.register.error_blocked_domain', { domain: blocked }));
        setLoading(false);
        return;
      }

      // Read referral code from URL param (priority) or dsm_ref cookie (fallback)
      const refParam = new URLSearchParams(window.location.search).get('ref');
      let referralCode: string | null = refParam;
      if (!referralCode) {
        const match = document.cookie.match(/(?:^|;\s*)dsm_ref=([^;]*)/);
        referralCode = match ? match[1] : null;
      }

      await api.post('/register', {
        name,
        admin_email: adminEmail,
        email_domains: domains,
        ...(referralCode ? { referral_code: referralCode } : {}),
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
    <AuthShell title={brandMsg.register.title} subtitle={brandMsg.register.subtitle} showBackToLogin={false}>
      {sent ? (
        <div className="rounded-lg border border-success/20 bg-success/10 p-4 text-center">
          <p className="text-sm font-medium text-success">{t('auth.register.success_title')}</p>
          <p className="mt-1 text-sm text-success">{t('auth.register.success_desc')}</p>
          <button
            type="button"
            disabled={resending || resent}
            onClick={async () => {
              setResending(true);
              try {
                await api.post('/auth/magic-link', { email: adminEmail });
                setResent(true);
                setTimeout(() => setResent(false), 30_000);
              } catch { /* ignore */ }
              setResending(false);
            }}
            className="mt-3 inline-block text-sm font-medium text-primary hover:underline disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {resent ? t('auth.register.resend_sent') : resending ? t('auth.register.resending') : t('auth.register.resend_link')}
          </button>
          <br />
          <Link to="/auth/login" className="mt-2 inline-block text-sm font-medium text-primary hover:underline">
            {t('auth.back_to_login')}
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}

          <div>
            <label htmlFor="company-name" className="block mb-1.5 text-muted-foreground">{t('auth.register.company_name')}</label>
            <input
              id="company-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('common.placeholder_company_name')}
              required
              className="w-full"
            />
          </div>

          <div>
            <label htmlFor="admin-email" className="block mb-1.5 text-muted-foreground">{t('auth.register.admin_email')}</label>
            <input
              id="admin-email"
              type="email"
              value={adminEmail}
              onChange={(e) => setAdminEmail(e.target.value)}
              placeholder={t('common.placeholder_admin_email')}
              required
              className="w-full"
            />
          </div>

          <div>
            <label htmlFor="domains" className="block mb-1.5 text-muted-foreground">{t('auth.register.allowed_domains')}</label>
            <input
              id="domains"
              type="text"
              value={emailDomains}
              onChange={(e) => setEmailDomains(e.target.value)}
              placeholder={t('common.placeholder_domains')}
              required
              className="w-full"
            />
            <p className="mt-1 text-xs text-muted-foreground">{t('auth.register.allowed_domains_help')}</p>
          </div>

          <label htmlFor="accept-terms" className="flex items-start gap-2.5 cursor-pointer">
            <input
              id="accept-terms"
              type="checkbox"
              checked={acceptedTerms}
              onChange={(e) => setAcceptedTerms(e.target.checked)}
              className="mt-0.5 h-4 w-4 shrink-0 rounded border-border accent-primary"
            />
            <span className="text-sm text-muted-foreground">
              {t('auth.register.accept_terms_prefix')}{' '}
              <a href={brandMsg.termsUrl} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{t('auth.terms.link')}</a>
              {' '}{t('common.and')}{' '}
              <a href={brandMsg.privacyUrl} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{t('auth.privacy.link')}</a>
            </span>
          </label>

          <button
            type="submit"
            disabled={loading || !acceptedTerms}
            className="h-9 w-full rounded-md bg-primary text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {loading ? t('auth.register.registering') : t('auth.register.register_company')}
          </button>

          <p className="text-center text-sm text-muted-foreground">
            {t('auth.register.already_have_account')}{' '}
            <Link to="/auth/login" className="font-medium text-primary hover:underline">{t('auth.login.sign_in')}</Link>
          </p>
        </form>
      )}
    </AuthShell>
  );
}
