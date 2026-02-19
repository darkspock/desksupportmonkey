import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { AuthShell } from '../../components/auth/AuthShell';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';
import { getDefaultRouteForRole } from '../../lib/navigation';
import { useI18n } from '../../lib/i18n';

export default function SetPasswordPage() {
  const { user, refreshUser } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!user) return <Navigate to="/auth/login" replace />;
  if (user.password_set) return <Navigate to={getDefaultRouteForRole(user.role)} replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError(t('auth.set_password.error_min_8'));
      return;
    }

    if (password !== confirm) {
      setError(t('auth.set_password.error_mismatch'));
      return;
    }

    setLoading(true);

    try {
      await api.post('/auth/set-password', { password });
      await refreshUser();
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('auth.set_password.error_failed');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title={t('auth.set_password.title')} subtitle={t('auth.set_password.subtitle')} showBackToLogin={false}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}

        <div>
          <label htmlFor="new-password" className="block mb-1.5 text-muted-foreground">{t('auth.set_password.new_password')}</label>
          <input
            id="new-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('auth.set_password.placeholder_min_8')}
            required
            className="w-full"
          />
        </div>

        <div>
          <label htmlFor="confirm-password" className="block mb-1.5 text-muted-foreground">{t('auth.set_password.confirm_password')}</label>
          <input
            id="confirm-password"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder={t('auth.set_password.placeholder_repeat')}
            required
            className="w-full"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="h-9 w-full rounded-md bg-primary text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {loading ? t('auth.set_password.saving') : t('auth.set_password.submit')}
        </button>
      </form>
    </AuthShell>
  );
}
