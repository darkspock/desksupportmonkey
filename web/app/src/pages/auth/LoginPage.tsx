import { useEffect, useMemo, useState } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { GoogleOAuthProvider, useGoogleLogin } from '@react-oauth/google';
import { AuthShell } from '../../components/auth/AuthShell';
import { MicrosoftIcon } from '../../components/icons/MicrosoftIcon';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';
import { fetchOAuthProviders, loginWithGoogle, loginWithMicrosoft, loginWithMicrosoftPopup } from '../../lib/oauth';
import { getDefaultRouteForRole, getSafeReturnTo } from '../../lib/navigation';
import { useI18n } from '../../lib/i18n';
import { getBrandMessages } from '../../config/brand';

type LoginMode = 'magic-link' | 'password';

function getAuthErrorMessage(
  err: unknown,
  fallback: string,
  invalidEmailMessage: string,
): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) {
    const normalized = detail.toLowerCase();
    if (normalized.includes('valid email address')) {
      return invalidEmailMessage;
    }
    return detail;
  }
  return fallback;
}

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? '';
const microsoftClientId = import.meta.env.VITE_MICROSOFT_CLIENT_ID ?? '';
const microsoftTenantId = import.meta.env.VITE_MICROSOFT_TENANT_ID ?? 'common';

function GoogleSignInButton({ onToken }: { onToken: (idToken: string) => void }) {
  const googleLogin = useGoogleLogin({
    onSuccess: (response) => {
      // useGoogleLogin with flow='auth-code' gives an authorization code.
      // For id_token we use the implicit flow (default) which gives access_token.
      // We need to use TokenResponse flow to exchange for id_token; use credential flow instead.
      onToken(response.access_token);
    },
    onError: () => {
      // Parent handles error state
    },
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
      Sign in with Google
    </button>
  );
}

export default function LoginPage() {
  const { user, login } = useAuth();
  const { t, language } = useI18n();
  const brandMsg = getBrandMessages(language);
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const returnTo = useMemo(() => getSafeReturnTo(params.get('returnTo')), [params]);

  const [mode, setMode] = useState<LoginMode>('magic-link');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const [microsoftEnabled, setMicrosoftEnabled] = useState(false);

  useEffect(() => {
    fetchOAuthProviders()
      .then((p) => {
        if (googleClientId) setGoogleEnabled(p.google);
        if (microsoftClientId) setMicrosoftEnabled(p.microsoft);
      })
      .catch(() => {/* ignore */});
  }, []);

  if (user) {
    return <Navigate to={returnTo ?? getDefaultRouteForRole(user.role)} replace />;
  }

  const handleGoogleToken = async (token: string) => {
    setError('');
    setLoading(true);
    try {
      const accessToken = await loginWithGoogle(token);
      await login(accessToken);
      navigate(returnTo ?? '/', { replace: true });
    } catch (err: unknown) {
      const msg = getAuthErrorMessage(err, t('auth.login.error_google_failed'), t('auth.login.error_invalid_email'));
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleMicrosoftLogin = async () => {
    setError('');
    setLoading(true);
    try {
      const idToken = await loginWithMicrosoftPopup(microsoftClientId, microsoftTenantId);
      const accessToken = await loginWithMicrosoft(idToken);
      await login(accessToken);
      navigate(returnTo ?? '/', { replace: true });
    } catch (err: unknown) {
      const msg = getAuthErrorMessage(err, t('auth.login.error_microsoft_failed'), t('auth.login.error_invalid_email'));
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/auth/magic-link', { email });
      setSent(true);
    } catch (err: unknown) {
      const msg = getAuthErrorMessage(
        err,
        t('auth.login.error_send_magic'),
        t('auth.login.error_invalid_email'),
      );
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post('/auth/login', { email, password });
      await login(data.data.access_token);
      navigate(returnTo ?? '/', { replace: true });
    } catch (err: unknown) {
      const msg = getAuthErrorMessage(
        err,
        t('auth.login.error_login_failed'),
        t('auth.login.error_invalid_email'),
      );
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
    <AuthShell title={brandMsg.login.title} subtitle={brandMsg.login.subtitle} showBackToLogin={false}>
      <div className="mb-6 grid grid-cols-2 rounded-xl border border-border bg-secondary p-1">
        <button
          type="button"
          onClick={() => {
            setMode('magic-link');
            setError('');
          }}
          className={`rounded-[10px] py-2.5 text-sm font-semibold transition-colors ${
            mode === 'magic-link'
              ? 'bg-card text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          {t('auth.login.magic_link')}
        </button>
        <button
          type="button"
          onClick={() => {
            setMode('password');
            setError('');
          }}
          className={`rounded-[10px] py-2.5 text-sm font-semibold transition-colors ${
            mode === 'password'
              ? 'bg-card text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          {t('auth.login.password')}
        </button>
      </div>

      {mode === 'magic-link' && sent ? (
        <div className="rounded-lg border border-success/20 bg-success/10 p-4 text-center">
          <p className="text-sm font-medium text-success">{t('auth.login.magic_sent')}</p>
          <p className="mt-1 text-sm text-success">{t('auth.login.magic_sent_desc')}</p>
          <button type="button" onClick={() => setSent(false)} className="mt-3 text-sm text-primary hover:underline">
            {t('auth.login.send_another')}
          </button>
        </div>
      ) : mode === 'magic-link' ? (
        <form onSubmit={handleMagicLink} className="space-y-4">
          {error && <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <div>
            <label htmlFor="email" className="block mb-1.5 text-muted-foreground">{t('auth.login.work_email')}</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('common.placeholder_work_email')}
              required
              className="w-full"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="h-9 w-full rounded-md bg-primary text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {loading ? t('auth.login.sending') : t('auth.login.send_magic_link')}
          </button>
        </form>
      ) : (
        <form onSubmit={handlePasswordLogin} className="space-y-4">
          {error && <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <div>
            <label htmlFor="email-password" className="block mb-1.5 text-muted-foreground">{t('auth.login.email')}</label>
            <input
              id="email-password"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('common.placeholder_work_email')}
              required
              className="w-full"
            />
          </div>
          <div>
            <label htmlFor="password" className="block mb-1.5 text-muted-foreground">{t('auth.login.password_label')}</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('auth.login.password_placeholder')}
              required
              className="w-full"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="h-9 w-full rounded-md bg-primary text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {loading ? t('auth.login.signing_in') : t('auth.login.sign_in')}
          </button>
          <p className="text-center text-xs text-muted-foreground">{t('auth.login.password_info')}</p>
        </form>
      )}

      {(googleEnabled || microsoftEnabled) && (
        <div className="mt-6">
          <div className="relative flex items-center gap-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground">{t('auth.login.or')}</span>
            <div className="h-px flex-1 bg-border" />
          </div>
          <div className="mt-3 flex flex-col gap-2">
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
                {t('auth.login.microsoft_signin')}
              </button>
            )}
          </div>
        </div>
      )}

      <p className="mt-7 text-center text-sm text-muted-foreground">
        {t('auth.login.need_workspace')}{' '}
        <Link to="/auth/register" className="font-medium text-primary hover:underline">{t('auth.login.register_company')}</Link>
      </p>

      <p className="mt-4 text-center text-xs text-muted-foreground">
        {t('auth.login.terms_notice')}{' '}
        <a href={brandMsg.termsUrl} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{t('auth.terms.link')}</a>
        {' '}{t('common.and')}{' '}
        <a href={brandMsg.privacyUrl} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{t('auth.privacy.link')}</a>
      </p>
    </AuthShell>
    </GoogleOAuthProvider>
  );
}
