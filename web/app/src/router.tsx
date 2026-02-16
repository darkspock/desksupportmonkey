/* eslint-disable react-refresh/only-export-components */
import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { PageLoading } from './components/ui/Loading';
import { RequireRole } from './components/auth/RequireRole';
import { RouteErrorBoundary } from './components/ui/RouteErrorBoundary';

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

const routeErrorElement = <RouteErrorBoundary />;

export const router = createBrowserRouter([
  { path: '/auth/login', element: <S><LoginPage /></S>, errorElement: routeErrorElement },
  { path: '/auth/register', element: <S><RegisterPage /></S>, errorElement: routeErrorElement },
  { path: '/auth/verify', element: <S><VerifyPage /></S>, errorElement: routeErrorElement },
  { path: '/auth/set-password', element: <S><SetPasswordPage /></S>, errorElement: routeErrorElement },
  // Legacy routes (redirect)
  { path: '/login', element: <Navigate to="/auth/login" replace />, errorElement: routeErrorElement },
  { path: '/verify', element: <Navigate to="/auth/verify" replace />, errorElement: routeErrorElement },
  {
    path: '/',
    element: <AppLayout />,
    errorElement: routeErrorElement,
    children: [
      // Employee (and auth users)
      { path: 'my/equipment', element: <S><MyEquipmentPage /></S> },
      { path: 'my/requests', element: <S><MyRequestsPage /></S> },
      { path: 'my/requests/new', element: <S><NewRequestPage /></S> },
      { path: 'my/notifications', element: <S><NotificationsPage /></S> },
      // Shared detail route (ownership validated by backend)
      { path: 'requests/:id', element: <S><RequestDetailPage /></S> },
      // Technician+
      {
        path: 'requests',
        element: <RequireRole roles={['technician', 'admin', 'super_admin']}><S><RequestQueuePage /></S></RequireRole>,
      },
      {
        path: 'assets',
        element: <RequireRole roles={['technician', 'admin', 'super_admin']}><S><AssetListPage /></S></RequireRole>,
      },
      {
        path: 'assets/new',
        element: <RequireRole roles={['technician', 'admin', 'super_admin']}><S><AssetFormPage /></S></RequireRole>,
      },
      {
        path: 'assets/import',
        element: <RequireRole roles={['technician', 'admin', 'super_admin']}><S><AssetImportPage /></S></RequireRole>,
      },
      {
        path: 'assets/:id',
        element: <RequireRole roles={['technician', 'admin', 'super_admin']}><S><AssetDetailPage /></S></RequireRole>,
      },
      // Admin+
      {
        path: 'dashboard',
        element: <RequireRole roles={['admin', 'super_admin']}><S><DashboardPage /></S></RequireRole>,
      },
      {
        path: 'users',
        element: <RequireRole roles={['admin', 'super_admin']}><S><UsersPage /></S></RequireRole>,
      },
      {
        path: 'departments',
        element: <RequireRole roles={['admin', 'super_admin']}><S><DepartmentsPage /></S></RequireRole>,
      },
      {
        path: 'reports',
        element: <RequireRole roles={['admin', 'super_admin']}><S><ReportsPage /></S></RequireRole>,
      },
      // Super Admin
      {
        path: 'companies',
        element: <RequireRole roles={['super_admin']}><S><CompaniesPage /></S></RequireRole>,
      },
    ],
  },
]);
