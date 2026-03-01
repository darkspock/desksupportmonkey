/**
 * Maps route path patterns to i18n help translation keys.
 * Order matters: more specific routes should come before their prefixes.
 */
export const HELP_CONTENT: Record<string, string> = {
  // Employee
  '/my/equipment': 'help.my_equipment',
  '/my/requests/new': 'help.new_request',
  '/my/requests': 'help.my_requests',
  '/my/notifications': 'help.notifications',
  '/my/appointments': 'help.my_appointments',
  '/my/shipments': 'help.my_shipments',
  '/my/incidents': 'help.my_incidents',
  '/my/report-incident': 'help.report_incident',
  '/my/maintenance': 'help.my_maintenance',
  '/my/tasks/requests': 'help.my_task_requests',
  '/my/tasks/appointments': 'help.my_task_appointments',
  '/knowledge-base': 'help.knowledge_base',

  // Technician
  '/requests': 'help.request_queue',
  '/assets/new': 'help.asset_new',
  '/assets/import': 'help.asset_import',
  '/assets': 'help.assets',
  '/calendar': 'help.calendar',
  '/shipments/new': 'help.shipment_new',
  '/shipments': 'help.shipments',
  '/maintenance/new': 'help.maintenance_new',
  '/maintenance': 'help.maintenance',
  '/incidents/dashboard': 'help.incident_dashboard',
  '/incidents/new': 'help.incident_new',
  '/incidents': 'help.incidents',
  '/kb/articles/new': 'help.kb_article_new',
  '/kb/categories': 'help.kb_categories',
  '/kb': 'help.kb_articles',
  '/risks/dashboard': 'help.risk_dashboard',
  '/risks/new': 'help.risk_new',
  '/risks': 'help.risks',
  '/vulnerabilities/dashboard': 'help.vulnerability_dashboard',
  '/vulnerabilities': 'help.vulnerabilities',
  '/changes/dashboard': 'help.change_dashboard',
  '/changes': 'help.changes',
  '/cmdb/dashboard': 'help.cmdb_dashboard',
  '/vendors/supply-chain': 'help.supply_chain',
  '/vendors': 'help.vendors',
  '/purchase-orders/new': 'help.purchase_order_new',
  '/purchase-orders': 'help.purchase_orders',
  '/addresses': 'help.addresses',
  '/settings/availability': 'help.availability',

  // Admin
  '/dashboard': 'help.dashboard',
  '/users/import': 'help.users_import',
  '/users': 'help.users',
  '/departments': 'help.departments',
  '/reports': 'help.reports',
  '/settings/company': 'help.company_settings',
  '/settings/api-keys': 'help.api_keys',
  '/settings/employee-roles': 'help.employee_roles',
  '/settings/equipment-profiles': 'help.equipment_profiles',
  '/settings/assignment-ai': 'help.assignment_ai',
  '/settings/request-classification': 'help.request_classification',
  '/settings/procurement': 'help.procurement_settings',
  '/settings/locations': 'help.locations',
  '/settings/compliance': 'help.compliance_controls',
  '/settings/gdpr': 'help.gdpr',
  '/settings/custom-fields': 'help.custom_fields',
  '/settings/asset-types': 'help.asset_types',
  '/settings/workflow-templates': 'help.workflow_templates',
  '/settings/nav-visibility': 'help.nav_visibility',
  '/maintenance-templates': 'help.maintenance_templates',
  '/billing/processing': 'help.billing_processing',
  '/billing': 'help.billing',
  '/sla/policies': 'help.sla_policies',
  '/sla/dashboard': 'help.sla_dashboard',
  '/audit': 'help.audit_log',
  '/compliance/dashboard': 'help.compliance_dashboard',

  // Super Admin
  '/overview': 'help.overview',
  '/companies': 'help.companies',
  '/super-admin/audit': 'help.super_admin_audit',

  // Onboarding
  '/onboarding': 'help.onboarding',
};

/**
 * Returns the i18n help key for a given pathname.
 * Tries exact match first, then prefix match (longest prefix wins).
 * Falls back to 'help.default'.
 */
export function getHelpKeyForPath(pathname: string): string {
  // Exact match
  if (HELP_CONTENT[pathname]) {
    return HELP_CONTENT[pathname];
  }

  // Prefix match — find longest matching prefix for detail pages like /assets/:id
  let bestMatch = '';
  let bestKey = 'help.default';

  for (const [pattern, key] of Object.entries(HELP_CONTENT)) {
    if (pathname.startsWith(pattern + '/') && pattern.length > bestMatch.length) {
      bestMatch = pattern;
      bestKey = key;
    }
  }

  return bestKey;
}
