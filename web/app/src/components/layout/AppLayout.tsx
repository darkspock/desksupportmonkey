import { useState } from 'react';
import { Outlet, Navigate, useLocation, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../contexts/AuthContext';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { PageLoading } from '../ui/Loading';
import { getDefaultRouteForRole } from '../../lib/navigation';
import { useNotificationRealtime } from '../../hooks/useNotificationRealtime';
import { useI18n } from '../../lib/i18n';
import api from '../../lib/api';

interface BillingStatus {
  billing_status: string;
  complimentary: boolean;
  grace_days_remaining: number | null;
}

function BillingBanner({ role }: { role: string }) {
  const { t } = useI18n();

  const { data } = useQuery<BillingStatus>({
    queryKey: ['billing-overview'],
    queryFn: async () => {
      const { data } = await api.get('/billing/');
      return data as BillingStatus;
    },
    // Silently skip on error (non-admins won't hit this, but guard anyway)
    retry: false,
    enabled: role === 'admin',
    staleTime: 30_000,
  });

  if (!data || data.complimentary) return null;
  if (data.billing_status === 'grace_period') {
    const days = data.grace_days_remaining ?? 0;
    return (
      <div className="w-full bg-yellow-500 px-4 py-2 text-center text-sm font-medium text-yellow-950">
        {t('page.billing.banner_grace', { days: String(days) })}{' '}
        <Link to="/billing" className="underline hover:no-underline">
          {t('page.billing.banner_action')}
        </Link>
      </div>
    );
  }
  if (data.billing_status === 'suspended') {
    return (
      <div className="w-full bg-red-600 px-4 py-2 text-center text-sm font-medium text-white">
        {t('page.billing.banner_suspended')}{' '}
        <Link to="/billing" className="underline hover:no-underline">
          {t('page.billing.banner_action')}
        </Link>
      </div>
    );
  }
  return null;
}

export function AppLayout() {
  const { user, loading, refreshUser } = useAuth();
  const location = useLocation();
  const { t } = useI18n();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [savingName, setSavingName] = useState(false);

  useNotificationRealtime();

  if (loading) return <PageLoading />;

  if (!user) {
    const returnTo = `${location.pathname}${location.search}${location.hash}`;
    return <Navigate to={`/auth/login?returnTo=${encodeURIComponent(returnTo)}`} replace />;
  }

  // Admin/super_admin/technician without password must set it first (skip if logged in via OAuth)
  if ((user.role === 'admin' || user.role === 'super_admin' || user.role === 'procurement_manager' || user.role === 'technician') && user.password_set === false && !user.has_oauth) {
    return <Navigate to="/auth/set-password" replace />;
  }

  // Super admin workspace is restricted to companies list.
  if (user.role === 'super_admin' && !location.pathname.startsWith('/companies')) {
    return <Navigate to="/companies" replace />;
  }

  if (location.pathname === '/') {
    return <Navigate to={getDefaultRouteForRole(user.role)} replace />;
  }

  const showNameModal = !user.name;

  const handleSaveName = async () => {
    if (!nameInput.trim() || savingName) return;
    setSavingName(true);
    try {
      await api.patch('/my/profile', { name: nameInput.trim() });
      await refreshUser();
    } finally {
      setSavingName(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar mobileOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
      <div className="min-w-0 flex-1 flex flex-col">
        <Header onMenuToggle={() => setMobileNavOpen(true)} />
        {user.role === 'admin' && <BillingBanner role={user.role} />}
        <main className="min-w-0 flex-1 p-4 md:p-6">
          <div className="mx-auto w-full max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>

      {showNameModal && (
        <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40" />
          <div className="relative z-[91] w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-foreground">
              {t('profile.complete_profile')}
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {t('profile.enter_name')}
            </p>
            <input
              type="text"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSaveName();
              }}
              placeholder={t('profile.full_name')}
              autoFocus
              maxLength={100}
              className="mt-4 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <div className="mt-5 flex justify-end">
              <button
                type="button"
                onClick={handleSaveName}
                disabled={!nameInput.trim() || savingName}
                className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium shadow-xs transition-all disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {savingName ? t('common.saving') : t('common.save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
