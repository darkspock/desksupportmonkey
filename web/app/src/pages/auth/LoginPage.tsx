import { useEffect, useMemo, useState } from 'react';
import { Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { GoogleOAuthProvider, useGoogleLogin } from '@react-oauth/google';
import { AuthShell } from '../../components/auth/AuthShell';
import { MicrosoftIcon } from '../../components/icons/MicrosoftIcon';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';
import { fetchOAuthProviders, loginWithGoogle, loginWithMicrosoft, loginWithMicrosoftPopup } from '../../lib/oauth';
import { getDefaultRouteForRole, getSafeReturnTo } from '../../lib/navigation';
import { useI18n } from '../../lib/i18n';
import { getBrandMessages } from '../../config/brand';

interface CompanyBySlug {
  id: string;
  name: string;
  slug: string;
  auth_mode: string;
  google_enabled: boolean;
  microsoft_enabled: boolean;
}

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
  const { slug } = useParams<{ slug?: string }>();

  const returnTo = useMemo(() => getSafeReturnTo(params.get('returnTo')), [params]);

  const [mode, setMode] = useState<LoginMode>('magic-link');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const [microsoftEnabled, setMicrosoftEnabled] = useState(false);
  const [companyInfo, setCompanyInfo] = useState<CompanyBySlug | null>(null);
  const [slugNotFound, setSlugNotFound] = useState(false);
  const [slugLoading, setSlugLoading] = useState(false);
  const [slugSearch, setSlugSearch] = useState('');

  // Fetch company info by slug
  useEffect(() => {
    if (!slug) return;
    setSlugLoading(true);
    setSlugNotFound(false);
    api.get(`/companies/by-slug/${slug}`)
      .then(({ data }) => {
        const company = data.data as CompanyBySlug;
        setCompanyInfo(company);
        if (googleClientId) setGoogleEnabled(company.google_enabled);
        if (microsoftClientId) setMicrosoftEnabled(company.microsoft_enabled);
      })
      .catch(() => {
        setSlugNotFound(true);
      })
      .finally(() => setSlugLoading(false));
  }, [slug]);

  // Fetch OAuth providers for non-slug login
  useEffect(() => {
    if (slug) return;
    fetchOAuthProviders()
      .then((p) => {
        if (googleClientId) setGoogleEnabled(p.google);
        if (microsoftClientId) setMicrosoftEnabled(p.microsoft);
      })
      .catch(() => {/* ignore */});
  }, [slug]);

  if (user) {
    if (user.role === 'admin' && user.needs_onboarding) {
      return <Navigate to="/onboarding" replace />;
    }
    return <Navigate to={returnTo ?? getDefaultRouteForRole(user.role)} replace />;
  }

  const navigateAfterLogin = async () => {
    const { data } = await api.get('/auth/me');
    const me = data.data;
    if (me.role === 'admin' && me.needs_onboarding) {
      navigate('/onboarding', { replace: true });
    } else {
      navigate(returnTo ?? '/', { replace: true });
    }
  };

  // Build slug-scoped auth paths
  const authPrefix = slug ? `/auth/${slug}` : '/auth';

  const handleMultiCompanyError = (err: unknown): boolean => {
    const resp = (err as { response?: { status?: number; data?: { detail?: string } } })?.response;
    if (resp?.status === 409) {
      try {
        const parsed = JSON.parse(resp.data?.detail ?? '{}');
        if (parsed.error === 'multiple_companies' && Array.isArray(parsed.slugs)) {
          setError(
            `Your email matches multiple companies. Please log in via your company page: ${parsed.slugs.join(', ')}`,
          );
          return true;
        }
      } catch {
        // Not a multi-company error
      }
    }
    return false;
  };

  const handleGoogleToken = async (token: string) => {
    setError('');
    setLoading(true);
    try {
      const accessToken = await loginWithGoogle(token, slug);
      await login(accessToken);
      await navigateAfterLogin();
    } catch (err: unknown) {
      if (!handleMultiCompanyError(err)) {
        const msg = getAuthErrorMessage(err, t('auth.login.error_google_failed'), t('auth.login.error_invalid_email'));
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMicrosoftLogin = async () => {
    setError('');
    setLoading(true);
    try {
      const idToken = await loginWithMicrosoftPopup(microsoftClientId, microsoftTenantId);
      const accessToken = await loginWithMicrosoft(idToken, slug);
      await login(accessToken);
      await navigateAfterLogin();
    } catch (err: unknown) {
      if (!handleMultiCompanyError(err)) {
        const msg = getAuthErrorMessage(err, t('auth.login.error_microsoft_failed'), t('auth.login.error_invalid_email'));
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post(`${authPrefix}/magic-link`, { email });
      setSent(true);
    } catch (err: unknown) {
      if (!handleMultiCompanyError(err)) {
        const msg = getAuthErrorMessage(
          err,
          t('auth.login.error_send_magic'),
          t('auth.login.error_invalid_email'),
        );
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post(`${authPrefix}/login`, { email, password });
      await login(data.data.access_token);
      await navigateAfterLogin();
    } catch (err: unknown) {
      if (!handleMultiCompanyError(err)) {
        const msg = getAuthErrorMessage(
          err,
          t('auth.login.error_login_failed'),
          t('auth.login.error_invalid_email'),
        );
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSlugSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = slugSearch.trim().toLowerCase();
    if (trimmed) {
      navigate(`/auth/login/${trimmed}`);
    }
  };

  // Slug loading state
  if (slug && slugLoading) {
    return (
      <AuthShell title={t('auth.slug.loading')} subtitle="" showBackToLogin={false}>
        <div className="flex justify-center py-8">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      </AuthShell>
    );
  }

  // Slug not found state
  if (slug && slugNotFound) {
    return (
      <AuthShell title={t('auth.slug.not_found_title')} subtitle="" showBackToLogin={false}>
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-center">
          <p className="text-sm font-medium text-destructive">{t('auth.slug.not_found')}</p>
        </div>
        <Link
          to="/auth/login"
          className="mt-4 block text-center text-sm font-medium text-primary hover:underline"
        >
          {t('auth.slug.back_to_login')}
        </Link>
      </AuthShell>
    );
  }

  // No slug — show company finder
  if (!slug && !companyInfo) {
    return (
      <GoogleOAuthProvider clientId={googleClientId}>
      <AuthShell title={brandMsg.login.title} subtitle={brandMsg.login.subtitle} showBackToLogin={false}>
        <form onSubmit={handleSlugSearch} className="mb-6 space-y-3">
          <label htmlFor="slug-search" className="block text-sm text-muted-foreground">
            {t('auth.slug.find_company')}
          </label>
          <input
            id="slug-search"
            type="text"
            value={slugSearch}
            onChange={(e) => setSlugSearch(e.target.value)}
            placeholder={t('auth.slug.find_placeholder')}
            className="w-full"
          />
          <button
            type="submit"
            disabled={!slugSearch.trim()}
            className="h-9 w-full rounded-md bg-primary text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            {t('auth.slug.find_button')}
          </button>
        </form>

        <div className="relative flex items-center gap-3 mb-6">
          <div className="h-px flex-1 bg-border" />
          <span className="text-xs text-muted-foreground">{t('auth.slug.or_login_directly')}</span>
          <div className="h-px flex-1 bg-border" />
        </div>

        <div className="mb-6 grid grid-cols-2 rounded-xl border border-border bg-secondary p-1">
          <button
            type="button"
            onClick={() => { setMode('magic-link'); setError(''); }}
            className={`rounded-[10px] py-2.5 text-sm font-semibold transition-colors ${mode === 'magic-link' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
          >
            {t('auth.login.magic_link')}
          </button>
          <button
            type="button"
            onClick={() => { setMode('password'); setError(''); }}
            className={`rounded-[10px] py-2.5 text-sm font-semibold transition-colors ${mode === 'password' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
          >
            {t('auth.login.password')}
          </button>
        </div>

        {mode === 'magic-link' && sent ? (
          <div className="rounded-lg border border-success/20 bg-success/10 p-4 text-center">
            <p className="text-sm font-medium text-success">{t('auth.login.magic_sent')}</p>
            <p className="mt-1 text-sm text-success">{t('auth.login.magic_sent_desc')}</p>
            <button type="button" onClick={() => setSent(false)} className="mt-3 text-sm text-primary hover:underline">{t('auth.login.send_another')}</button>
          </div>
        ) : mode === 'magic-link' ? (
          <form onSubmit={handleMagicLink} className="space-y-4">
            {error && <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
            <div>
              <label htmlFor="email" className="block mb-1.5 text-muted-foreground">{t('auth.login.work_email')}</label>
              <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t('common.placeholder_work_email')} required className="w-full" />
            </div>
            <button type="submit" disabled={loading} className="h-9 w-full rounded-md bg-primary text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50">
              {loading ? t('auth.login.sending') : t('auth.login.send_magic_link')}
            </button>
          </form>
        ) : (
          <form onSubmit={handlePasswordLogin} className="space-y-4">
            {error && <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
            <div>
              <label htmlFor="email-password" className="block mb-1.5 text-muted-foreground">{t('auth.login.email')}</label>
              <input id="email-password" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t('common.placeholder_work_email')} required className="w-full" />
            </div>
            <div>
              <label htmlFor="password" className="block mb-1.5 text-muted-foreground">{t('auth.login.password_label')}</label>
              <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t('auth.login.password_placeholder')} required className="w-full" />
            </div>
            <button type="submit" disabled={loading} className="h-9 w-full rounded-md bg-primary text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50">
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
              {googleEnabled && googleClientId && <GoogleSignInButton onToken={handleGoogleToken} />}
              {microsoftEnabled && microsoftClientId && (
                <button type="button" onClick={handleMicrosoftLogin} disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium text-foreground shadow-xs transition hover:bg-secondary disabled:pointer-events-none disabled:opacity-50">
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

  // Slug-based login — company resolved
  const title = companyInfo ? companyInfo.name : brandMsg.login.title;
  const subtitle = companyInfo ? t('auth.slug.sign_in_to', { company: companyInfo.name }) : brandMsg.login.subtitle;

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
    <AuthShell title={title} subtitle={subtitle} showBackToLogin={false}>
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

      {slug && (
        <p className="mt-5 text-center text-sm text-muted-foreground">
          <Link to="/auth/login" className="font-medium text-primary hover:underline">{t('auth.slug.different_company')}</Link>
        </p>
      )}

      <p className="mt-4 text-center text-sm text-muted-foreground">
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
