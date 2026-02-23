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
const ChangePasswordPage = lazy(() => import('./pages/auth/ChangePasswordPage'));
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
const CompanySettingsPage = lazy(() => import('./pages/admin/CompanySettingsPage'));
const ApiKeysPage = lazy(() => import('./pages/admin/ApiKeysPage'));
const EquipmentProfilesPage = lazy(() => import('./pages/admin/EquipmentProfilesPage'));
const EmployeeRolesPage = lazy(() => import('./pages/admin/EmployeeRolesPage'));
const AssignmentAISettingsPage = lazy(() => import('./pages/admin/AssignmentAISettingsPage'));
const ClassificationSettingsPage = lazy(() => import('./pages/admin/ClassificationSettingsPage'));
const ProcurementSettingsPage = lazy(() => import('./pages/admin/ProcurementSettingsPage'));
const VendorListPage = lazy(() => import('./pages/admin/VendorListPage'));
const PurchaseOrderListPage = lazy(() => import('./pages/admin/PurchaseOrderListPage'));
const PurchaseOrderDetailPage = lazy(() => import('./pages/admin/PurchaseOrderDetailPage'));
const PurchaseOrderFormPage = lazy(() => import('./pages/admin/PurchaseOrderFormPage'));
const CalendarPage = lazy(() => import('./pages/technician/CalendarPage'));
const AvailabilitySettingsPage = lazy(() => import('./pages/technician/AvailabilitySettingsPage'));
const MyAppointmentsPage = lazy(() => import('./pages/employee/MyAppointmentsPage'));
const MyShipmentsPage = lazy(() => import('./pages/employee/MyShipmentsPage'));
const ShipmentsPage = lazy(() => import('./pages/technician/ShipmentsPage'));
const ShipmentDetailPage = lazy(() => import('./pages/technician/ShipmentDetailPage'));
const ShipmentCreatePage = lazy(() => import('./pages/technician/ShipmentCreatePage'));
const AddressesPage = lazy(() => import('./pages/technician/AddressesPage'));
const MaintenancePage = lazy(() => import('./pages/technician/MaintenancePage'));
const MaintenanceDetailPage = lazy(() => import('./pages/technician/MaintenanceDetailPage'));
const MaintenanceFormPage = lazy(() => import('./pages/technician/MaintenanceFormPage'));
const MyMaintenancePage = lazy(() => import('./pages/technician/MyMaintenancePage'));
const MyTaskAppointmentsPage = lazy(() => import('./pages/technician/MyTaskAppointmentsPage'));
const MaintenanceTemplatesPage = lazy(() => import('./pages/admin/MaintenanceTemplatesPage'));
const UserImportPage = lazy(() => import('./pages/admin/UserImportPage'));
const CompaniesPage = lazy(() => import('./pages/superadmin/CompaniesPage'));
const FounderDashboardPage = lazy(() => import('./pages/superadmin/FounderDashboardPage'));
const BillingPage = lazy(() => import('./pages/admin/BillingPage'));
const BillingProcessingPage = lazy(() => import('./pages/admin/BillingProcessingPage'));

function S({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoading />}>{children}</Suspense>;
}

const routeErrorElement = <RouteErrorBoundary />;

export const router = createBrowserRouter([
  { path: '/auth/login', element: <S><LoginPage /></S>, errorElement: routeErrorElement },
  { path: '/auth/register', element: <S><RegisterPage /></S>, errorElement: routeErrorElement },
  { path: '/auth/verify', element: <S><VerifyPage /></S>, errorElement: routeErrorElement },
  { path: '/auth/set-password', element: <S><SetPasswordPage /></S>, errorElement: routeErrorElement },
  { path: '/auth/change-password', element: <S><ChangePasswordPage /></S>, errorElement: routeErrorElement },
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
      { path: 'my/appointments', element: <S><MyAppointmentsPage /></S> },
      { path: 'my/shipments', element: <S><MyShipmentsPage /></S> },
      {
        path: 'my/maintenance',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><MyMaintenancePage /></S></RequireRole>,
      },
      {
        path: 'my/tasks/appointments',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><MyTaskAppointmentsPage /></S></RequireRole>,
      },
      // Shared detail route (ownership validated by backend)
      { path: 'requests/:id', element: <S><RequestDetailPage /></S> },
      // Technician+
      {
        path: 'requests',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><RequestQueuePage /></S></RequireRole>,
      },
      {
        path: 'vendors',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><VendorListPage /></S></RequireRole>,
      },
      {
        path: 'purchase-orders',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><PurchaseOrderListPage /></S></RequireRole>,
      },
      {
        path: 'purchase-orders/new',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><PurchaseOrderFormPage /></S></RequireRole>,
      },
      {
        path: 'purchase-orders/:id',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><PurchaseOrderDetailPage /></S></RequireRole>,
      },
      {
        path: 'purchase-orders/:id/edit',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><PurchaseOrderFormPage /></S></RequireRole>,
      },
      {
        path: 'calendar',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><CalendarPage /></S></RequireRole>,
      },
      {
        path: 'settings/availability',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><AvailabilitySettingsPage /></S></RequireRole>,
      },
      {
        path: 'shipments',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><ShipmentsPage /></S></RequireRole>,
      },
      {
        path: 'shipments/new',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><ShipmentCreatePage /></S></RequireRole>,
      },
      {
        path: 'shipments/:id',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><ShipmentDetailPage /></S></RequireRole>,
      },
      {
        path: 'addresses',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><AddressesPage /></S></RequireRole>,
      },
      {
        path: 'maintenance',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><MaintenancePage /></S></RequireRole>,
      },
      {
        path: 'maintenance/new',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><MaintenanceFormPage /></S></RequireRole>,
      },
      {
        path: 'maintenance/:id',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><MaintenanceDetailPage /></S></RequireRole>,
      },
      {
        path: 'maintenance/:id/edit',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><MaintenanceFormPage /></S></RequireRole>,
      },
      {
        path: 'assets',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><AssetListPage /></S></RequireRole>,
      },
      {
        path: 'assets/new',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><AssetFormPage /></S></RequireRole>,
      },
      {
        path: 'assets/import',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><AssetImportPage /></S></RequireRole>,
      },
      {
        path: 'assets/:id',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><AssetDetailPage /></S></RequireRole>,
      },
      // Admin+
      {
        path: 'dashboard',
        element: <RequireRole roles={['admin', 'super_admin']}><S><DashboardPage /></S></RequireRole>,
      },
      {
        path: 'users/import',
        element: <RequireRole roles={['admin', 'super_admin']}><S><UserImportPage /></S></RequireRole>,
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
      {
        path: 'settings/company',
        element: <RequireRole roles={['admin']}><S><CompanySettingsPage /></S></RequireRole>,
      },
      {
        path: 'settings/api-keys',
        element: <RequireRole roles={['admin', 'super_admin']}><S><ApiKeysPage /></S></RequireRole>,
      },
      {
        path: 'settings/employee-roles',
        element: <RequireRole roles={['admin', 'super_admin']}><S><EmployeeRolesPage /></S></RequireRole>,
      },
      {
        path: 'settings/equipment-profiles',
        element: <RequireRole roles={['admin', 'super_admin']}><S><EquipmentProfilesPage /></S></RequireRole>,
      },
      {
        path: 'settings/assignment-ai',
        element: <RequireRole roles={['admin']}><S><AssignmentAISettingsPage /></S></RequireRole>,
      },
      {
        path: 'settings/request-classification',
        element: <RequireRole roles={['admin']}><S><ClassificationSettingsPage /></S></RequireRole>,
      },
      {
        path: 'settings/procurement',
        element: <RequireRole roles={['admin']}><S><ProcurementSettingsPage /></S></RequireRole>,
      },
      {
        path: 'maintenance-templates',
        element: <RequireRole roles={['admin', 'super_admin']}><S><MaintenanceTemplatesPage /></S></RequireRole>,
      },
      // Admin billing
      {
        path: 'billing',
        element: <RequireRole roles={['admin']}><S><BillingPage /></S></RequireRole>,
      },
      {
        path: 'billing/processing',
        element: <RequireRole roles={['admin']}><S><BillingProcessingPage /></S></RequireRole>,
      },
      // Super Admin
      {
        path: 'overview',
        element: <RequireRole roles={['super_admin']}><S><FounderDashboardPage /></S></RequireRole>,
      },
      {
        path: 'companies',
        element: <RequireRole roles={['super_admin']}><S><CompaniesPage /></S></RequireRole>,
      },
    ],
  },
]);
