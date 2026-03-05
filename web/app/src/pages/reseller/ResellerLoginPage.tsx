import { useEffect, useMemo, useState } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { GoogleOAuthProvider, useGoogleLogin } from '@react-oauth/google';
import { AuthShell } from '../../components/auth/AuthShell';
import { MicrosoftIcon } from '../../components/icons/MicrosoftIcon';
import { useResellerAuth } from '../../contexts/ResellerAuthContext';
import api from '../../lib/api';
import { fetchOAuthProviders, loginWithMicrosoftPopup } from '../../lib/oauth';
import { useI18n } from '../../lib/i18n';

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? '';
const microsoftClientId = import.meta.env.VITE_MICROSOFT_CLIENT_ID ?? '';
const microsoftTenantId = import.meta.env.VITE_MICROSOFT_TENANT_ID ?? 'common';

function getAuthErrorMessage(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  return fallback;
}

function GoogleSignInButton({ onToken }: { onToken: (idToken: string) => void }) {
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
      className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium text-foreground shadow-xs transition hover:bg-secondary"
    >
      <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
        <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
        <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
        <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
        <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
        <path fill="none" d="M0 0h48v48H0z"/>
      </svg>
      {t('reseller.login.google_signin')}
    </button>
  );
}

function ResellerLoginContent() {
  const { reseller, login } = useResellerAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const returnTo = useMemo(() => {
    const val = params.get('returnTo');
    if (!val || !val.startsWith('/reseller/')) return null;
    return val;
  }, [params]);

  const resetSuccess = params.get('reset') === 'success';

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const [microsoftEnabled, setMicrosoftEnabled] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  useEffect(() => {
    fetchOAuthProviders()
      .then((p) => {
        if (googleClientId) setGoogleEnabled(p.google);
        if (microsoftClientId) setMicrosoftEnabled(p.microsoft);
      })
      .catch(() => {});
  }, []);

  if (reseller) {
    return <Navigate to={returnTo ?? '/reseller/dashboard'} replace />;
  }

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post<{ data: { access_token: string } }>('/reseller/auth/login', {
        email: loginEmail,
        password: loginPassword,
      });
      await login(data.data.access_token);
      navigate(returnTo ?? '/reseller/dashboard', { replace: true });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      if (typeof detail === 'string' && detail.includes('pending')) {
        setError(t('reseller.login.pending_approval'));
      } else {
        setError(getAuthErrorMessage(err, t('reseller.login.error_password')));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleToken = async (token: string) => {
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post<{ data: { access_token: string } }>('/reseller/auth/google', {
        id_token: token,
      });
      await login(data.data.access_token);
      navigate(returnTo ?? '/reseller/dashboard', { replace: true });
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, t('reseller.login.error_google')));
    } finally {
      setLoading(false);
    }
  };

  const handleMicrosoftLogin = async () => {
    setError('');
    setLoading(true);
    try {
      const idToken = await loginWithMicrosoftPopup(microsoftClientId, microsoftTenantId);
      const { data } = await api.post<{ data: { access_token: string } }>('/reseller/auth/microsoft', {
        id_token: idToken,
      });
      await login(data.data.access_token);
      navigate(returnTo ?? '/reseller/dashboard', { replace: true });
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, t('reseller.login.error_microsoft')));
    } finally {
      setLoading(false);
    }
  };

  const hasOAuth = googleEnabled || microsoftEnabled;

  return (
    <AuthShell
      title={t('reseller.login.title')}
      subtitle={t('reseller.login.subtitle')}
      showBackToLogin={false}
    >
      <div className="space-y-4">
        {resetSuccess && (
          <p className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
            {t('reseller.reset_password.success')}
          </p>
        )}

        {error && (
          <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        {/* Email/Password Login */}
        <form onSubmit={handlePasswordLogin} className="space-y-3">
          <div>
            <label htmlFor="login-email" className="block mb-1.5 text-sm text-muted-foreground">
              {t('reseller.login.email')}
            </label>
            <input
              id="login-email"
              type="email"
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
              required
              className="w-full"
              placeholder="you@company.com"
            />
          </div>
          <div>
            <label htmlFor="login-password" className="block mb-1.5 text-sm text-muted-foreground">
              {t('reseller.login.password')}
            </label>
            <input
              id="login-password"
              type="password"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              required
              className="w-full"
            />
          </div>
          <div className="flex justify-end">
            <Link to="/reseller/forgot-password" className="text-xs text-primary hover:underline">
              {t('reseller.login.forgot_password')}
            </Link>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? t('common.working') : t('reseller.login.submit')}
          </button>
        </form>

        {/* Divider */}
        {hasOAuth && (
          <div className="relative flex items-center py-1">
            <div className="grow border-t border-border" />
            <span className="mx-3 shrink text-xs text-muted-foreground">{t('common.or')}</span>
            <div className="grow border-t border-border" />
          </div>
        )}

        {/* OAuth buttons */}
        <div className="flex flex-col gap-2">
          {googleEnabled && googleClientId && (
            <GoogleSignInButton onToken={handleGoogleToken} />
          )}
          {microsoftEnabled && microsoftClientId && (
            <button
              type="button"
              onClick={handleMicrosoftLogin}
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium text-foreground shadow-xs transition hover:bg-secondary disabled:pointer-events-none disabled:opacity-50"
            >
              <MicrosoftIcon />
              {t('reseller.login.microsoft_signin')}
            </button>
          )}
        </div>

        <div className="space-y-2 pt-2">
          <p className="text-center text-sm text-muted-foreground">
            {t('reseller.login.no_account')}{' '}
            <Link to="/reseller/register" className="font-medium text-primary hover:underline">
              {t('reseller.login.apply_here')}
            </Link>
          </p>
          <p className="text-center text-xs text-muted-foreground">
            {t('reseller.login.not_a_reseller')}{' '}
            <a href="/auth/login" className="font-medium text-primary hover:underline">
              {t('reseller.login.user_login')}
            </a>
          </p>
        </div>
      </div>
    </AuthShell>
  );
}

export default function ResellerLoginPage() {
  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <ResellerLoginContent />
    </GoogleOAuthProvider>
  );
}
