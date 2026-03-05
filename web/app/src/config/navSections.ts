export interface NavItem {
  type?: undefined;
  to: string;
  labelKey: string;
  roles?: string[];
}

export interface NavSeparator {
  type: 'separator';
  roles?: string[];
}

export interface NavSubGroup {
  type: 'subgroup';
  labelKey: string;
  roles?: string[];
  items: NavItem[];
}

export type NavEntry = NavItem | NavSeparator | NavSubGroup;

export interface NavSection {
  labelKey?: string;
  items: NavEntry[];
}

export const sections: NavSection[] = [
  {
    labelKey: 'nav.section_my_activity',
    items: [
      { to: '/my/equipment', labelKey: 'nav.my_equipment' },
      { to: '/my/requests', labelKey: 'nav.my_requests' },
      { to: '/my/appointments', labelKey: 'nav.my_appointments' },
      { to: '/my/shipments', labelKey: 'nav.my_shipments' },
      { to: '/my/incidents', labelKey: 'nav.my_incidents' },
    ],
  },
  {
    labelKey: 'nav.section_my_tasks',
    items: [
      { to: '/my/tasks/requests', labelKey: 'nav.my_assigned_requests', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/my/tasks/appointments', labelKey: 'nav.my_task_appointments', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/my/maintenance', labelKey: 'nav.my_maintenance', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
    ],
  },
  {
    labelKey: 'nav.section_operations',
    items: [
      { to: '/dashboard', labelKey: 'nav.dashboard', roles: ['admin', 'super_admin'] },
      { to: '/requests', labelKey: 'nav.request_queue', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/calendar', labelKey: 'nav.calendar', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/assets', labelKey: 'nav.asset_inventory', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/vendors', labelKey: 'nav.vendors', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/purchase-orders', labelKey: 'nav.purchase_orders', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/shipments', labelKey: 'nav.shipments', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/maintenance', labelKey: 'nav.maintenance', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
    ],
  },
  {
    labelKey: 'nav.section_knowledge',
    items: [
      { to: '/knowledge-base', labelKey: 'nav.knowledge_base' },
      { to: '/kb', labelKey: 'nav.kb_management', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/kb/categories', labelKey: 'nav.kb_categories', roles: ['admin', 'super_admin'] },
    ],
  },
  {
    labelKey: 'nav.section_security',
    items: [
      { to: '/audit', labelKey: 'nav.audit_log', roles: ['admin', 'super_admin'] },
      { to: '/incidents', labelKey: 'nav.incidents', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/incidents/dashboard', labelKey: 'nav.incident_dashboard', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/risks', labelKey: 'nav.risks', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/risks/dashboard', labelKey: 'nav.risk_dashboard', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
      { to: '/vulnerabilities', labelKey: 'nav.vulnerabilities', roles: ['admin', 'super_admin'] },
      { to: '/vulnerabilities/dashboard', labelKey: 'nav.vulnerability_dashboard', roles: ['admin', 'super_admin'] },
      { to: '/compliance/dashboard', labelKey: 'nav.compliance_dashboard', roles: ['admin', 'super_admin'] },
    ],
  },
  {
    labelKey: 'nav.section_management',
    items: [
      {
        type: 'subgroup', labelKey: 'nav.subgroup_people', roles: ['admin', 'super_admin'],
        items: [
          { to: '/users', labelKey: 'nav.users', roles: ['admin', 'super_admin'] },
          { to: '/departments', labelKey: 'nav.departments', roles: ['admin', 'super_admin'] },
          { to: '/settings/employee-roles', labelKey: 'nav.employee_roles', roles: ['admin', 'super_admin'] },
          { to: '/settings/gdpr', labelKey: 'nav.gdpr_requests', roles: ['admin'] },
        ],
      },
      {
        type: 'subgroup', labelKey: 'nav.subgroup_configuration', roles: ['admin'],
        items: [
          { to: '/settings/company', labelKey: 'nav.company_settings', roles: ['admin'] },
          { to: '/settings/locations', labelKey: 'nav.locations', roles: ['admin'] },
          { to: '/settings/compliance', labelKey: 'nav.compliance_controls', roles: ['admin'] },
          { to: '/settings/request-classification', labelKey: 'nav.request_classification', roles: ['admin'] },
          { to: '/maintenance-templates', labelKey: 'nav.maintenance_templates', roles: ['admin', 'super_admin'] },
          { to: '/settings/assignment-ai', labelKey: 'nav.assignment_ai', roles: ['admin'] },
          { to: '/settings/availability', labelKey: 'nav.availability_settings', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
        ],
      },
      {
        type: 'subgroup', labelKey: 'nav.subgroup_procurement', roles: ['admin'],
        items: [
          { to: '/settings/equipment-profiles', labelKey: 'nav.equipment_profiles', roles: ['admin', 'super_admin'] },
          { to: '/settings/procurement', labelKey: 'nav.procurement_settings', roles: ['admin'] },
        ],
      },
      {
        type: 'subgroup', labelKey: 'nav.subgroup_customization', roles: ['admin', 'super_admin'],
        items: [
          { to: '/settings/asset-types', labelKey: 'nav.asset_types', roles: ['admin', 'super_admin'] },
          { to: '/settings/custom-fields', labelKey: 'nav.custom_fields', roles: ['admin', 'super_admin'] },
          { to: '/settings/workflow-templates', labelKey: 'nav.workflow_templates', roles: ['admin', 'super_admin'] },
          { to: '/settings/nav-visibility', labelKey: 'nav.nav_visibility', roles: ['admin'] },
        ],
      },
      {
        type: 'subgroup', labelKey: 'nav.subgroup_advanced', roles: ['admin', 'super_admin'],
        items: [
          { to: '/settings/api-keys', labelKey: 'nav.api_keys', roles: ['admin', 'super_admin'] },
        ],
      },
      {
        type: 'subgroup', labelKey: 'nav.subgroup_sla', roles: ['admin', 'super_admin'],
        items: [
          { to: '/sla/policies', labelKey: 'nav.sla_policies', roles: ['admin', 'super_admin'] },
          { to: '/sla/dashboard', labelKey: 'nav.sla_dashboard', roles: ['admin', 'super_admin'] },
        ],
      },
      {
        type: 'subgroup', labelKey: 'nav.subgroup_changes', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'],
        items: [
          { to: '/changes', labelKey: 'nav.changes', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
          { to: '/changes/dashboard', labelKey: 'nav.change_dashboard', roles: ['admin', 'super_admin'] },
        ],
      },
      { to: '/billing', labelKey: 'nav.billing', roles: ['admin'] },
      {
        type: 'subgroup', labelKey: 'nav.subgroup_reports', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'],
        items: [
          { to: '/reports', labelKey: 'nav.reports', roles: ['admin', 'super_admin'] },
          { to: '/vendors/supply-chain', labelKey: 'nav.supply_chain_risk', roles: ['technician', 'procurement_manager', 'admin', 'super_admin'] },
          { to: '/cmdb/dashboard', labelKey: 'nav.cmdb_dashboard', roles: ['admin', 'super_admin'] },
        ],
      },
    ],
  },
  {
    labelKey: 'nav.section_platform',
    items: [
      { to: '/overview', labelKey: 'nav.overview', roles: ['super_admin'] },
      { to: '/companies', labelKey: 'nav.companies', roles: ['super_admin'] },
      { to: '/resellers', labelKey: 'nav.resellers', roles: ['super_admin'] },
      { to: '/platform/support-tickets', labelKey: 'nav.platform_support_tickets', roles: ['super_admin'] },
      { to: '/super-admin/audit', labelKey: 'nav.super_admin_audit', roles: ['super_admin'] },
    ],
  },
];
