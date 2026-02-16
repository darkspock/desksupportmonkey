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
        {error && <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <div>
          <label htmlFor="change-new-password" className="mb-1 block text-sm font-medium text-slate-700">{t('auth.change_password.new_password')}</label>
          <input
            id="change-new-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('auth.change_password.placeholder_min_8')}
            required
            className="h-11 w-full rounded-xl border border-slate-300 px-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </div>

        <div>
          <label htmlFor="change-confirm-password" className="mb-1 block text-sm font-medium text-slate-700">{t('auth.change_password.confirm_password')}</label>
          <input
            id="change-confirm-password"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder={t('auth.change_password.placeholder_repeat')}
            required
            className="h-11 w-full rounded-xl border border-slate-300 px-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="h-11 w-full rounded-xl bg-blue-600 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? t('auth.change_password.saving') : t('auth.change_password.submit')}
        </button>
      </form>
    </AuthShell>
  );
}
