import { useMemo, useState } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthShell } from '../../components/auth/AuthShell';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';
import { getDefaultRouteForRole, getSafeReturnTo } from '../../lib/navigation';
import { useI18n } from '../../lib/i18n';

type LoginMode = 'magic-link' | 'password';

export default function LoginPage() {
  const { user, login } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const returnTo = useMemo(() => getSafeReturnTo(params.get('returnTo')), [params]);

  const [mode, setMode] = useState<LoginMode>('magic-link');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) {
    return <Navigate to={returnTo ?? getDefaultRouteForRole(user.role)} replace />;
  }

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/auth/magic-link', { email });
      setSent(true);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('auth.login.error_send_magic');
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
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('auth.login.error_login_failed');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title={t('auth.login.title')} subtitle={t('auth.login.subtitle')} showBackToLogin={false}>
      <div className="mb-6 grid grid-cols-2 rounded-xl border border-slate-200 bg-slate-100 p-1">
        <button
          type="button"
          onClick={() => {
            setMode('magic-link');
            setError('');
          }}
          className={`rounded-[10px] py-2.5 text-sm font-semibold transition-colors ${
            mode === 'magic-link'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
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
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          {t('auth.login.password')}
        </button>
      </div>

      {mode === 'magic-link' && sent ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-center">
          <p className="text-sm font-medium text-emerald-800">{t('auth.login.magic_sent')}</p>
          <p className="mt-1 text-sm text-emerald-700">{t('auth.login.magic_sent_desc')}</p>
          <button type="button" onClick={() => setSent(false)} className="mt-3 text-sm text-blue-700 hover:underline">
            {t('auth.login.send_another')}
          </button>
        </div>
      ) : mode === 'magic-link' ? (
        <form onSubmit={handleMagicLink} className="space-y-4">
          {error && <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">{t('auth.login.work_email')}</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('common.placeholder_work_email')}
              required
              className="h-11 w-full rounded-xl border border-slate-300 px-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="h-11 w-full rounded-xl bg-blue-600 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? t('auth.login.sending') : t('auth.login.send_magic_link')}
          </button>
        </form>
      ) : (
        <form onSubmit={handlePasswordLogin} className="space-y-4">
          {error && <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div>
            <label htmlFor="email-password" className="mb-1 block text-sm font-medium text-slate-700">{t('auth.login.email')}</label>
            <input
              id="email-password"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('common.placeholder_work_email')}
              required
              className="h-11 w-full rounded-xl border border-slate-300 px-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">{t('auth.login.password_label')}</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('auth.login.password_placeholder')}
              required
              className="h-11 w-full rounded-xl border border-slate-300 px-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="h-11 w-full rounded-xl bg-blue-600 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? t('auth.login.signing_in') : t('auth.login.sign_in')}
          </button>
          <p className="text-center text-xs text-slate-500">{t('auth.login.password_info')}</p>
        </form>
      )}

      <p className="mt-7 text-center text-sm text-slate-600">
        {t('auth.login.need_workspace')}{' '}
        <Link to="/auth/register" className="font-medium text-blue-700 hover:underline">{t('auth.login.register_company')}</Link>
      </p>
    </AuthShell>
  );
}
