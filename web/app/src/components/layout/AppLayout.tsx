import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { PageLoading } from '../ui/Loading';

export function AppLayout() {
  const { user, loading } = useAuth();

  if (loading) return <PageLoading />;
  if (!user) return <Navigate to="/login" replace />;

  // Admin/super_admin without password must set it first
  if ((user.role === 'admin' || user.role === 'super_admin') && user.password_set === false) {
    return <Navigate to="/set-password" replace />;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
