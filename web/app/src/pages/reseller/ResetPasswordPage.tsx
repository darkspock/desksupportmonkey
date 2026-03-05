import { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { AuthShell } from '../../components/auth/AuthShell';
import { useI18n } from '../../lib/i18n';
import api from '../../lib/api';

export default function ResellerResetPasswordPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!token) {
    return (
      <AuthShell title={t('reseller.reset_password.title')} subtitle="" showBackToLogin={false}>
        <div className="space-y-4 text-center">
          <p className="text-sm text-destructive">{t('reseller.reset_password.invalid_token')}</p>
          <Link to="/reseller/login" className="text-sm font-medium text-primary hover:underline">
            {t('reseller.register.login_link')}
          </Link>
        </div>
      </AuthShell>
    );
  }

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
      await api.post('/reseller/auth/reset-password', { token, password });
      navigate('/reseller/login?reset=success', { replace: true });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title={t('reseller.reset_password.title')} subtitle="" showBackToLogin={false}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div>
          <label htmlFor="rp-password" className="block mb-1.5 text-sm text-muted-foreground">
            {t('reseller.reset_password.new_password')}
          </label>
          <input
            id="rp-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className="w-full"
          />
        </div>

        <div>
          <label htmlFor="rp-confirm" className="block mb-1.5 text-sm text-muted-foreground">
            {t('reseller.reset_password.confirm_password')}
          </label>
          <input
            id="rp-confirm"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
            className="w-full"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? t('common.working') : t('reseller.reset_password.submit')}
        </button>
      </form>
    </AuthShell>
  );
}
