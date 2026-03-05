import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { GoogleOAuthProvider, useGoogleLogin } from '@react-oauth/google';
import { AuthShell } from '../../components/auth/AuthShell';
import { MicrosoftIcon } from '../../components/icons/MicrosoftIcon';
import { useI18n } from '../../lib/i18n';
import { getBrandMessages } from '../../config/brand';
import { fetchOAuthProviders, loginWithMicrosoftPopup } from '../../lib/oauth';
import api from '../../lib/api';

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? '';
const microsoftClientId = import.meta.env.VITE_MICROSOFT_CLIENT_ID ?? '';
const microsoftTenantId = import.meta.env.VITE_MICROSOFT_TENANT_ID ?? 'common';

function GoogleRegisterButton({ onToken, disabled }: { onToken: (idToken: string) => void; disabled: boolean }) {
  const { t } = useI18n();
  const googleLogin = useGoogleLogin({
    onSuccess: (response) => {
      onToken(response.access_token);
    },
    onError: () => {},
  });
  return (
    <button
      type="button"
      onClick={() => googleLogin()}
      disabled={disabled}
      className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium text-foreground shadow-xs transition hover:bg-secondary disabled:pointer-events-none disabled:opacity-50"
    >
      <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
        <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
        <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
        <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
        <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
        <path fill="none" d="M0 0h48v48H0z"/>
      </svg>
      {t('reseller.register.google_signup')}
    </button>
  );
}

function ResellerRegisterContent() {
  const { t, language } = useI18n();
  const brandMsg = getBrandMessages(language);
  const [companyName, setCompanyName] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const [microsoftEnabled, setMicrosoftEnabled] = useState(false);

  useEffect(() => {
    fetchOAuthProviders()
      .then((p) => {
        if (googleClientId) setGoogleEnabled(p.google);
        if (microsoftClientId) setMicrosoftEnabled(p.microsoft);
      })
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError(t('auth.set_password.error_mismatch'));
      return;
    }

    if (password.length < 8) {
      setError(t('reseller.register.password_min_length'));
      return;
    }

    setLoading(true);
    try {
      await api.post('/reseller/auth/register', {
        name,
        email,
        company_name: companyName,
        password,
      });
      setSuccess(true);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const validateCompanyName = (): boolean => {
    if (!companyName.trim()) {
      setError(t('reseller.register.company_required'));
      return false;
    }
    if (!acceptedTerms) {
      setError(t('reseller.register.terms_required'));
      return false;
    }
    return true;
  };

  const handleGoogleToken = async (token: string) => {
    if (!validateCompanyName()) return;
    setError('');
    setLoading(true);
    try {
      await api.post('/reseller/auth/register/google', {
        id_token: token,
        company_name: companyName,
      });
      setSuccess(true);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleMicrosoftRegister = async () => {
    if (!validateCompanyName()) return;
    setError('');
    setLoading(true);
    try {
      const idToken = await loginWithMicrosoftPopup(microsoftClientId, microsoftTenantId);
      await api.post('/reseller/auth/register/microsoft', {
        id_token: idToken,
        company_name: companyName,
      });
      setSuccess(true);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const hasOAuth = googleEnabled || microsoftEnabled;

  if (success) {
    return (
      <AuthShell title={t('reseller.register.success_title')} subtitle="" showBackToLogin={false}>
        <div className="space-y-4 text-center">
          <div className="rounded-lg border border-green-200 bg-green-50 p-4">
            <p className="text-sm text-green-800">{t('reseller.register.success_message')}</p>
          </div>
          <Link to="/reseller/login" className="text-sm font-medium text-primary hover:underline">
            {t('reseller.register.login_link')}
          </Link>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell title={t('reseller.register.title')} subtitle={t('reseller.register.subtitle')} showBackToLogin={false}>
      <div className="space-y-4">
        {error && (
          <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        {/* Company name first — required for both password and OAuth registration */}
        <div>
          <label htmlFor="reg-company" className="block mb-1.5 text-sm text-muted-foreground">
            {t('reseller.register.company_name')}
          </label>
          <input
            id="reg-company"
            type="text"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            required
            className="w-full"
            placeholder="Acme Inc"
          />
        </div>

        {/* OAuth registration buttons */}
        {hasOAuth && (
          <>
            <div className="flex flex-col gap-2">
              {googleEnabled && googleClientId && (
                <GoogleRegisterButton onToken={handleGoogleToken} disabled={loading} />
              )}
              {microsoftEnabled && microsoftClientId && (
                <button
                  type="button"
                  onClick={handleMicrosoftRegister}
                  disabled={loading}
                  className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium text-foreground shadow-xs transition hover:bg-secondary disabled:pointer-events-none disabled:opacity-50"
                >
                  <MicrosoftIcon />
                  {t('reseller.register.microsoft_signup')}
                </button>
              )}
            </div>

            <div className="relative flex items-center py-1">
              <div className="grow border-t border-border" />
              <span className="mx-3 shrink text-xs text-muted-foreground">{t('common.or')}</span>
              <div className="grow border-t border-border" />
            </div>
          </>
        )}

        {/* Password registration form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="reg-name" className="block mb-1.5 text-sm text-muted-foreground">
              {t('reseller.register.name')}
            </label>
            <input
              id="reg-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full"
              placeholder="John Smith"
            />
          </div>

          <div>
            <label htmlFor="reg-email" className="block mb-1.5 text-sm text-muted-foreground">
              {t('reseller.register.email')}
            </label>
            <input
              id="reg-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full"
              placeholder="you@company.com"
            />
          </div>

          <div>
            <label htmlFor="reg-password" className="block mb-1.5 text-sm text-muted-foreground">
              {t('reseller.register.password')}
            </label>
            <input
              id="reg-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full"
            />
            <p className="mt-1 text-xs text-muted-foreground">{t('reseller.register.password_min_length')}</p>
          </div>

          <div>
            <label htmlFor="reg-confirm" className="block mb-1.5 text-sm text-muted-foreground">
              {t('reseller.register.confirm_password')}
            </label>
            <input
              id="reg-confirm"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
              className="w-full"
            />
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
              {t('reseller.register.accept_terms_prefix')}{' '}
              <a href={brandMsg.termsUrl} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{t('auth.terms.link')}</a>
              {' '}{t('common.and')}{' '}
              <a href={brandMsg.privacyUrl} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{t('auth.privacy.link')}</a>
              {', '}{t('reseller.register.and_read')}{' '}
              <a href="/reseller/terms" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{t('reseller.register.reseller_terms_link')}</a>
            </span>
          </label>

          <button
            type="submit"
            disabled={loading || !acceptedTerms}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? t('common.working') : t('reseller.register.submit')}
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          {t('reseller.register.have_account')}{' '}
          <Link to="/reseller/login" className="font-medium text-primary hover:underline">
            {t('reseller.register.login_link')}
          </Link>
        </p>
      </div>
    </AuthShell>
  );
}

export default function ResellerRegisterPage() {
  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <ResellerRegisterContent />
    </GoogleOAuthProvider>
  );
}
