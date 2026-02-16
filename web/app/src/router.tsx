import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { PageLoading } from './components/ui/Loading';

// Lazy-loaded pages
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'));
const VerifyPage = lazy(() => import('./pages/auth/VerifyPage'));
const SetPasswordPage = lazy(() => import('./pages/auth/SetPasswordPage'));
const MyEquipmentPage = lazy(() => import('./pages/employee/MyEquipmentPage'));
const MyRequestsPage = lazy(() => import('./pages/employee/MyRequestsPage'));
const NewRequestPage = lazy(() => import('./pages/employee/NewRequestPage'));
const NotificationsPage = lazy(() => import('./pages/employee/NotificationsPage'));
const RequestQueuePage = lazy(() => import('./pages/technician/RequestQueuePage'));
const RequestDetailPage = lazy(() => import('./pages/technician/RequestDetailPage'));
const AssetListPage = lazy(() => import('./pages/technician/AssetListPage'));
const AssetDetailPage = lazy(() => import('./pages/technician/AssetDetailPage'));
const AssetFormPage = lazy(() => import('./pages/technician/AssetFormPage'));
const AssetImportPage = lazy(() => import('./pages/technician/AssetImportPage'));
const DashboardPage = lazy(() => import('./pages/admin/DashboardPage'));
const UsersPage = lazy(() => import('./pages/admin/UsersPage'));
const DepartmentsPage = lazy(() => import('./pages/admin/DepartmentsPage'));
const ReportsPage = lazy(() => import('./pages/admin/ReportsPage'));
const CompaniesPage = lazy(() => import('./pages/superadmin/CompaniesPage'));

function S({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoading />}>{children}</Suspense>;
}

export const router = createBrowserRouter([
  { path: '/login', element: <S><LoginPage /></S> },
  { path: '/register', element: <S><RegisterPage /></S> },
  { path: '/verify', element: <S><VerifyPage /></S> },
  { path: '/set-password', element: <S><SetPasswordPage /></S> },
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/my/equipment" replace /> },
      // Employee
      { path: 'my/equipment', element: <S><MyEquipmentPage /></S> },
      { path: 'my/requests', element: <S><MyRequestsPage /></S> },
      { path: 'my/requests/new', element: <S><NewRequestPage /></S> },
      { path: 'my/notifications', element: <S><NotificationsPage /></S> },
      // Technician+
      { path: 'requests', element: <S><RequestQueuePage /></S> },
      { path: 'requests/:id', element: <S><RequestDetailPage /></S> },
      { path: 'assets', element: <S><AssetListPage /></S> },
      { path: 'assets/new', element: <S><AssetFormPage /></S> },
      { path: 'assets/import', element: <S><AssetImportPage /></S> },
      { path: 'assets/:id', element: <S><AssetDetailPage /></S> },
      // Admin+
      { path: 'dashboard', element: <S><DashboardPage /></S> },
      { path: 'users', element: <S><UsersPage /></S> },
      { path: 'departments', element: <S><DepartmentsPage /></S> },
      { path: 'reports', element: <S><ReportsPage /></S> },
      // Super Admin
      { path: 'companies', element: <S><CompaniesPage /></S> },
    ],
  },
]);
