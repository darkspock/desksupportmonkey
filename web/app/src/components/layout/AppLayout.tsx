import { useState } from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { PageLoading } from '../ui/Loading';
import { getDefaultRouteForRole } from '../../lib/navigation';
import { useNotificationRealtime } from '../../hooks/useNotificationRealtime';

export function AppLayout() {
  const { user, loading } = useAuth();
  const location = useLocation();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useNotificationRealtime();

  if (loading) return <PageLoading />;

  if (!user) {
    const returnTo = `${location.pathname}${location.search}${location.hash}`;
    return <Navigate to={`/auth/login?returnTo=${encodeURIComponent(returnTo)}`} replace />;
  }

  // Admin/super_admin without password must set it first
  if ((user.role === 'admin' || user.role === 'super_admin') && user.password_set === false) {
    return <Navigate to="/auth/set-password" replace />;
  }

  if (location.pathname === '/') {
    return <Navigate to={getDefaultRouteForRole(user.role)} replace />;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar mobileOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
      <div className="min-w-0 flex-1 flex flex-col">
        <Header onMenuToggle={() => setMobileNavOpen(true)} />
        <main className="min-w-0 flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
