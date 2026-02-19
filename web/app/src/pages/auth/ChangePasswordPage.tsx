import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { AuthShell } from '../../components/auth/AuthShell';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../lib/api';
import { getDefaultRouteForRole } from '../../lib/navigation';
import { useI18n } from '../../lib/i18n';

export default function ChangePasswordPage() {
  const { user, refreshUser } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!user) return <Navigate to="/auth/login" replace />;
  if (user.role !== 'admin' && user.role !== 'super_admin') {
    return <Navigate to={getDefaultRouteForRole(user.role)} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError(t('auth.change_password.error_min_8'));
      return;
    }

    if (password !== confirm) {
      setError(t('auth.change_password.error_mismatch'));
      return;
    }

    setLoading(true);

    try {
      await api.post('/auth/set-password', { password });
      await refreshUser();
      navigate(getDefaultRouteForRole(user.role), { replace: true });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || t('auth.change_password.error_failed');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title={t('auth.change_password.title')} subtitle={t('auth.change_password.subtitle')} showBackToLogin={false}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}

        <div>
          <label htmlFor="change-new-password" className="block mb-1.5 text-muted-foreground">{t('auth.change_password.new_password')}</label>
          <input
            id="change-new-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('auth.change_password.placeholder_min_8')}
            required
            className="w-full"
          />
        </div>

        <div>
          <label htmlFor="change-confirm-password" className="block mb-1.5 text-muted-foreground">{t('auth.change_password.confirm_password')}</label>
          <input
            id="change-confirm-password"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder={t('auth.change_password.placeholder_repeat')}
            required
            className="w-full"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="h-9 w-full rounded-md bg-primary text-sm font-medium text-primary-foreground shadow-xs transition-all hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          {loading ? t('auth.change_password.saving') : t('auth.change_password.submit')}
        </button>
      </form>
    </AuthShell>
  );
}
