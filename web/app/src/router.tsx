/* eslint-disable react-refresh/only-export-components */
import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { PageLoading } from './components/ui/Loading';
import { RequireRole } from './components/auth/RequireRole';
import { RouteErrorBoundary } from './components/ui/RouteErrorBoundary';

// Auto-reload once on stale chunk after deployment (no infinite loop — sessionStorage guard)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function lazyWithRetry(importFn: () => Promise<{ default: React.ComponentType<any> }>) {
  return lazy(() =>
    importFn().catch(() => {
      const key = 'chunk_reload';
      if (!sessionStorage.getItem(key)) {
        sessionStorage.setItem(key, '1');
        window.location.reload();
        return new Promise(() => {}); // never resolves — reload in progress
      }
      sessionStorage.removeItem(key);
      return importFn(); // second attempt: let it fail naturally to show error boundary
    }),
  );
}

// Lazy-loaded pages
const LoginPage = lazyWithRetry(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazyWithRetry(() => import('./pages/auth/RegisterPage'));
const VerifyPage = lazyWithRetry(() => import('./pages/auth/VerifyPage'));
const SetPasswordPage = lazyWithRetry(() => import('./pages/auth/SetPasswordPage'));
const ChangePasswordPage = lazyWithRetry(() => import('./pages/auth/ChangePasswordPage'));
const MyEquipmentPage = lazyWithRetry(() => import('./pages/employee/MyEquipmentPage'));
const MyRequestsPage = lazyWithRetry(() => import('./pages/employee/MyRequestsPage'));
const NewRequestPage = lazyWithRetry(() => import('./pages/employee/NewRequestPage'));
const NotificationsPage = lazyWithRetry(() => import('./pages/employee/NotificationsPage'));
const RequestQueuePage = lazyWithRetry(() => import('./pages/technician/RequestQueuePage'));
const RequestDetailPage = lazyWithRetry(() => import('./pages/technician/RequestDetailPage'));
const AssetListPage = lazyWithRetry(() => import('./pages/technician/AssetListPage'));
const AssetDetailPage = lazyWithRetry(() => import('./pages/technician/AssetDetailPage'));
const AssetFormPage = lazyWithRetry(() => import('./pages/technician/AssetFormPage'));
const AssetImportPage = lazyWithRetry(() => import('./pages/technician/AssetImportPage'));
const DashboardPage = lazyWithRetry(() => import('./pages/admin/DashboardPage'));
const UsersPage = lazyWithRetry(() => import('./pages/admin/UsersPage'));
const DepartmentsPage = lazyWithRetry(() => import('./pages/admin/DepartmentsPage'));
const ReportsPage = lazyWithRetry(() => import('./pages/admin/ReportsPage'));
const CompanySettingsPage = lazyWithRetry(() => import('./pages/admin/CompanySettingsPage'));
const ApiKeysPage = lazyWithRetry(() => import('./pages/admin/ApiKeysPage'));
const EquipmentProfilesPage = lazyWithRetry(() => import('./pages/admin/EquipmentProfilesPage'));
const EmployeeRolesPage = lazyWithRetry(() => import('./pages/admin/EmployeeRolesPage'));
const AssignmentAISettingsPage = lazyWithRetry(() => import('./pages/admin/AssignmentAISettingsPage'));
const ClassificationSettingsPage = lazyWithRetry(() => import('./pages/admin/ClassificationSettingsPage'));
const ProcurementSettingsPage = lazyWithRetry(() => import('./pages/admin/ProcurementSettingsPage'));
const VendorListPage = lazyWithRetry(() => import('./pages/admin/VendorListPage'));
const VendorDetailPage = lazyWithRetry(() => import('./pages/admin/VendorDetailPage'));
const PurchaseOrderListPage = lazyWithRetry(() => import('./pages/admin/PurchaseOrderListPage'));
const PurchaseOrderDetailPage = lazyWithRetry(() => import('./pages/admin/PurchaseOrderDetailPage'));
const PurchaseOrderFormPage = lazyWithRetry(() => import('./pages/admin/PurchaseOrderFormPage'));
const CalendarPage = lazyWithRetry(() => import('./pages/technician/CalendarPage'));
const AvailabilitySettingsPage = lazyWithRetry(() => import('./pages/technician/AvailabilitySettingsPage'));
const MyAppointmentsPage = lazyWithRetry(() => import('./pages/employee/MyAppointmentsPage'));
const MyRequestDetailPage = lazyWithRetry(() => import('./pages/employee/MyRequestDetailPage'));
const MyShipmentsPage = lazyWithRetry(() => import('./pages/employee/MyShipmentsPage'));
const ShipmentsPage = lazyWithRetry(() => import('./pages/technician/ShipmentsPage'));
const ShipmentDetailPage = lazyWithRetry(() => import('./pages/technician/ShipmentDetailPage'));
const ShipmentCreatePage = lazyWithRetry(() => import('./pages/technician/ShipmentCreatePage'));
const AddressesPage = lazyWithRetry(() => import('./pages/technician/AddressesPage'));
const MaintenancePage = lazyWithRetry(() => import('./pages/technician/MaintenancePage'));
const MaintenanceDetailPage = lazyWithRetry(() => import('./pages/technician/MaintenanceDetailPage'));
const MaintenanceFormPage = lazyWithRetry(() => import('./pages/technician/MaintenanceFormPage'));
const MyMaintenancePage = lazyWithRetry(() => import('./pages/technician/MyMaintenancePage'));
const MyAssignedRequestsPage = lazyWithRetry(() => import('./pages/technician/MyAssignedRequestsPage'));
const MyTaskAppointmentsPage = lazyWithRetry(() => import('./pages/technician/MyTaskAppointmentsPage'));
const MaintenanceTemplatesPage = lazyWithRetry(() => import('./pages/admin/MaintenanceTemplatesPage'));
const ReportIncidentPage = lazyWithRetry(() => import('./pages/employee/ReportIncidentPage'));
const MyIncidentsPage = lazyWithRetry(() => import('./pages/employee/MyIncidentsPage'));
const IncidentDashboardPage = lazyWithRetry(() => import('./pages/technician/IncidentDashboardPage'));
const IncidentsListPage = lazyWithRetry(() => import('./pages/technician/IncidentsList'));
const IncidentDetailPage = lazyWithRetry(() => import('./pages/technician/IncidentDetail'));
const CreateIncidentPage = lazyWithRetry(() => import('./pages/technician/CreateIncidentPage'));
const RiskListPage = lazyWithRetry(() => import('./pages/technician/RiskListPage'));
const RiskDetailPage = lazyWithRetry(() => import('./pages/technician/RiskDetailPage'));
const CreateRiskPage = lazyWithRetry(() => import('./pages/technician/CreateRiskPage'));
const EditRiskPage = lazyWithRetry(() => import('./pages/technician/EditRiskPage'));
const RiskDashboardPage = lazyWithRetry(() => import('./pages/technician/RiskDashboardPage'));
const KBCategoriesPage = lazyWithRetry(() => import('./pages/admin/KBCategoriesPage'));
const KBArticleListPage = lazyWithRetry(() => import('./pages/technician/KBArticleListPage'));
const KBArticleDetailPage = lazyWithRetry(() => import('./pages/technician/KBArticleDetailPage'));
const CreateArticlePage = lazyWithRetry(() => import('./pages/technician/CreateArticlePage'));
const EditArticlePage = lazyWithRetry(() => import('./pages/technician/EditArticlePage'));
const KBArticleVersionsPage = lazyWithRetry(() => import('./pages/technician/KBArticleVersionsPage'));
const KnowledgeBasePage = lazyWithRetry(() => import('./pages/employee/KnowledgeBasePage'));
const UserImportPage = lazyWithRetry(() => import('./pages/admin/UserImportPage'));
const CompaniesPage = lazyWithRetry(() => import('./pages/superadmin/CompaniesPage'));
const FounderDashboardPage = lazyWithRetry(() => import('./pages/superadmin/FounderDashboardPage'));
const BillingPage = lazyWithRetry(() => import('./pages/admin/BillingPage'));
const SlaPoliciesPage = lazyWithRetry(() => import('./pages/admin/SlaPoliciesPage'));
const SlaDashboardPage = lazyWithRetry(() => import('./pages/admin/SlaDashboardPage'));
const LocationsPage = lazyWithRetry(() => import('./pages/admin/LocationsPage'));
const AuditLogPage = lazyWithRetry(() => import('./pages/admin/AuditLogPage'));
const AuditEntryDetailPage = lazyWithRetry(() => import('./pages/admin/AuditEntryDetailPage'));
const ComplianceControlsPage = lazyWithRetry(() => import('./pages/admin/ComplianceControlsPage'));
const CrossCompanyAuditPage = lazyWithRetry(() => import('./pages/superadmin/CrossCompanyAuditPage'));
const GdprRequestsPage = lazyWithRetry(() => import('./pages/admin/GdprRequestsPage'));
const ComplianceDashboardPage = lazyWithRetry(() => import('./pages/admin/ComplianceDashboardPage'));
const CustomFieldsPage = lazyWithRetry(() => import('./pages/admin/CustomFieldsPage'));
const AssetTypesPage = lazyWithRetry(() => import('./pages/admin/AssetTypesPage'));
const WorkflowTemplatesPage = lazyWithRetry(() => import('./pages/admin/WorkflowTemplatesPage'));
const NavVisibilitySettingsPage = lazyWithRetry(() => import('./pages/admin/NavVisibilitySettingsPage'));
const SupplyChainDashboardPage = lazyWithRetry(() => import('./pages/admin/SupplyChainDashboardPage'));
const VulnerabilitiesPage = lazyWithRetry(() => import('./pages/admin/VulnerabilitiesPage'));
const VulnerabilityDetailPage = lazyWithRetry(() => import('./pages/admin/VulnerabilityDetailPage'));
const CMDBDashboardPage = lazyWithRetry(() => import('./pages/admin/CMDBDashboardPage'));
const VulnerabilityDashboardPage = lazyWithRetry(() => import('./pages/admin/VulnerabilityDashboardPage'));
const ChangeListPage = lazyWithRetry(() => import('./pages/admin/ChangeListPage'));
const ChangeDetailPage = lazyWithRetry(() => import('./pages/admin/ChangeDetailPage'));
const ChangeDashboardPage = lazyWithRetry(() => import('./pages/admin/ChangeDashboardPage'));
const OnboardingWizardPage = lazyWithRetry(() => import('./pages/admin/OnboardingWizardPage'));

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
      { path: 'my/requests/:id', element: <S><MyRequestDetailPage /></S> },
      { path: 'my/shipments', element: <S><MyShipmentsPage /></S> },
      { path: 'my/incidents', element: <S><MyIncidentsPage /></S> },
      { path: 'knowledge-base', element: <S><KnowledgeBasePage /></S> },
      { path: 'my/report-incident', element: <S><ReportIncidentPage /></S> },
      {
        path: 'my/maintenance',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><MyMaintenancePage /></S></RequireRole>,
      },
      {
        path: 'my/tasks/requests',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><MyAssignedRequestsPage /></S></RequireRole>,
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
        path: 'vendors/supply-chain',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><SupplyChainDashboardPage /></S></RequireRole>,
      },
      {
        path: 'cmdb/dashboard',
        element: <RequireRole roles={['admin', 'super_admin']}><S><CMDBDashboardPage /></S></RequireRole>,
      },
      {
        path: 'vendors/:id',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><VendorDetailPage /></S></RequireRole>,
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
        path: 'incidents',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><IncidentsListPage /></S></RequireRole>,
      },
      {
        path: 'incidents/dashboard',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><IncidentDashboardPage /></S></RequireRole>,
      },
      {
        path: 'incidents/new',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><CreateIncidentPage /></S></RequireRole>,
      },
      {
        path: 'incidents/:id',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><IncidentDetailPage /></S></RequireRole>,
      },
      {
        path: 'kb',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><KBArticleListPage /></S></RequireRole>,
      },
      {
        path: 'kb/articles/new',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><CreateArticlePage /></S></RequireRole>,
      },
      {
        path: 'kb/articles/:id',
        element: <S><KBArticleDetailPage /></S>,
      },
      {
        path: 'kb/articles/:id/edit',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><EditArticlePage /></S></RequireRole>,
      },
      {
        path: 'kb/articles/:id/versions',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><KBArticleVersionsPage /></S></RequireRole>,
      },
      {
        path: 'kb/categories',
        element: <RequireRole roles={['admin', 'super_admin']}><S><KBCategoriesPage /></S></RequireRole>,
      },
      {
        path: 'risks',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><RiskListPage /></S></RequireRole>,
      },
      {
        path: 'risks/dashboard',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><RiskDashboardPage /></S></RequireRole>,
      },
      {
        path: 'risks/new',
        element: <RequireRole roles={['admin', 'super_admin']}><S><CreateRiskPage /></S></RequireRole>,
      },
      {
        path: 'risks/:id',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><RiskDetailPage /></S></RequireRole>,
      },
      {
        path: 'risks/:id/edit',
        element: <RequireRole roles={['admin', 'super_admin']}><S><EditRiskPage /></S></RequireRole>,
      },
      {
        path: 'vulnerabilities',
        element: <RequireRole roles={['admin', 'super_admin']}><S><VulnerabilitiesPage /></S></RequireRole>,
      },
      {
        path: 'vulnerabilities/dashboard',
        element: <RequireRole roles={['admin', 'super_admin']}><S><VulnerabilityDashboardPage /></S></RequireRole>,
      },
      {
        path: 'vulnerabilities/:id',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><VulnerabilityDetailPage /></S></RequireRole>,
      },
      {
        path: 'changes',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><ChangeListPage /></S></RequireRole>,
      },
      {
        path: 'changes/dashboard',
        element: <RequireRole roles={['admin', 'super_admin']}><S><ChangeDashboardPage /></S></RequireRole>,
      },
      {
        path: 'changes/:id',
        element: <RequireRole roles={['technician', 'procurement_manager', 'admin', 'super_admin']}><S><ChangeDetailPage /></S></RequireRole>,
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
      // Onboarding wizard (admin only)
      {
        path: 'onboarding',
        element: <RequireRole roles={['admin']}><S><OnboardingWizardPage /></S></RequireRole>,
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
      // Admin billing (Community Edition info)
      {
        path: 'billing',
        element: <RequireRole roles={['admin']}><S><BillingPage /></S></RequireRole>,
      },
      {
        path: 'sla/policies',
        element: <RequireRole roles={['admin', 'super_admin']}><S><SlaPoliciesPage /></S></RequireRole>,
      },
      {
        path: 'sla/dashboard',
        element: <RequireRole roles={['admin', 'super_admin']}><S><SlaDashboardPage /></S></RequireRole>,
      },
      {
        path: 'settings/locations',
        element: <RequireRole roles={['admin']}><S><LocationsPage /></S></RequireRole>,
      },
      {
        path: 'audit',
        element: <RequireRole roles={['admin', 'super_admin']}><S><AuditLogPage /></S></RequireRole>,
      },
      {
        path: 'audit/:id',
        element: <RequireRole roles={['admin', 'super_admin']}><S><AuditEntryDetailPage /></S></RequireRole>,
      },
      {
        path: 'settings/compliance',
        element: <RequireRole roles={['admin']}><S><ComplianceControlsPage /></S></RequireRole>,
      },
      {
        path: 'settings/gdpr',
        element: <RequireRole roles={['admin']}><S><GdprRequestsPage /></S></RequireRole>,
      },
      {
        path: 'compliance/dashboard',
        element: <RequireRole roles={['admin', 'super_admin']}><S><ComplianceDashboardPage /></S></RequireRole>,
      },
      {
        path: 'settings/custom-fields',
        element: <RequireRole roles={['admin', 'super_admin']}><S><CustomFieldsPage /></S></RequireRole>,
      },
      {
        path: 'settings/asset-types',
        element: <RequireRole roles={['admin', 'super_admin']}><S><AssetTypesPage /></S></RequireRole>,
      },
      {
        path: 'settings/workflow-templates',
        element: <RequireRole roles={['admin', 'super_admin']}><S><WorkflowTemplatesPage /></S></RequireRole>,
      },
      {
        path: 'settings/nav-visibility',
        element: <RequireRole roles={['admin']}><S><NavVisibilitySettingsPage /></S></RequireRole>,
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
      {
        path: 'super-admin/audit',
        element: <RequireRole roles={['super_admin']}><S><CrossCompanyAuditPage /></S></RequireRole>,
      },
    ],
  },
]);
