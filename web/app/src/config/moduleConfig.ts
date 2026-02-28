export interface ModuleDefinition {
  id: string;
  labelKey: string;
  descriptionKey: string;
  always_on: boolean;
  navPaths: string[];
}

export interface SectorDefinition {
  id: string;
  labelKey: string;
}

export interface FrameworkDefinition {
  key: string;
  name: string;
  color: string;
}

export const MODULES: ModuleDefinition[] = [
  {
    id: 'service_desk',
    labelKey: 'onboarding.modules.service_desk',
    descriptionKey: 'onboarding.modules.service_desk_desc',
    always_on: true,
    navPaths: ['/sla/policies', '/sla/dashboard'],
  },
  {
    id: 'asset_inventory',
    labelKey: 'onboarding.modules.asset_inventory',
    descriptionKey: 'onboarding.modules.asset_inventory_desc',
    always_on: false,
    navPaths: ['/assets', '/cmdb/dashboard'],
  },
  {
    id: 'procurement',
    labelKey: 'onboarding.modules.procurement',
    descriptionKey: 'onboarding.modules.procurement_desc',
    always_on: false,
    navPaths: ['/purchase-orders', '/vendors', '/vendors/supply-chain', '/settings/procurement', '/settings/equipment-profiles'],
  },
  {
    id: 'knowledge_base',
    labelKey: 'onboarding.modules.knowledge_base',
    descriptionKey: 'onboarding.modules.knowledge_base_desc',
    always_on: false,
    navPaths: ['/knowledge-base', '/kb', '/kb/categories'],
  },
  {
    id: 'compliance_audit',
    labelKey: 'onboarding.modules.compliance_audit',
    descriptionKey: 'onboarding.modules.compliance_audit_desc',
    always_on: false,
    navPaths: ['/compliance/dashboard', '/settings/compliance', '/audit'],
  },
  {
    id: 'security',
    labelKey: 'onboarding.modules.security',
    descriptionKey: 'onboarding.modules.security_desc',
    always_on: false,
    navPaths: ['/incidents', '/incidents/dashboard', '/risks', '/risks/dashboard', '/vulnerabilities', '/vulnerabilities/dashboard'],
  },
  {
    id: 'change_management',
    labelKey: 'onboarding.modules.change_management',
    descriptionKey: 'onboarding.modules.change_management_desc',
    always_on: false,
    navPaths: ['/changes', '/changes/dashboard'],
  },
  {
    id: 'maintenance',
    labelKey: 'onboarding.modules.maintenance',
    descriptionKey: 'onboarding.modules.maintenance_desc',
    always_on: false,
    navPaths: ['/maintenance', '/my/maintenance', '/maintenance-templates'],
  },
  {
    id: 'logistics',
    labelKey: 'onboarding.modules.logistics',
    descriptionKey: 'onboarding.modules.logistics_desc',
    always_on: false,
    navPaths: ['/shipments', '/my/shipments', '/my/appointments', '/my/tasks/appointments', '/calendar'],
  },
];

export const SECTORS: SectorDefinition[] = [
  { id: 'financial_services', labelKey: 'onboarding.sectors.financial_services' },
  { id: 'healthcare', labelKey: 'onboarding.sectors.healthcare' },
  { id: 'government', labelKey: 'onboarding.sectors.government' },
  { id: 'education', labelKey: 'onboarding.sectors.education' },
  { id: 'technology', labelKey: 'onboarding.sectors.technology' },
  { id: 'manufacturing', labelKey: 'onboarding.sectors.manufacturing' },
  { id: 'retail', labelKey: 'onboarding.sectors.retail' },
  { id: 'energy', labelKey: 'onboarding.sectors.energy' },
  { id: 'telecommunications', labelKey: 'onboarding.sectors.telecommunications' },
  { id: 'professional_services', labelKey: 'onboarding.sectors.professional_services' },
  { id: 'logistics', labelKey: 'onboarding.sectors.logistics' },
  { id: 'other', labelKey: 'onboarding.sectors.other' },
];

export const SECTOR_FRAMEWORKS: Record<string, string[]> = {
  financial_services: ['DORA', 'NIS2', 'ISO 27001', 'GDPR'],
  healthcare: ['NIS2', 'ISO 27001', 'GDPR'],
  government: ['NIS2', 'ISO 27001', 'GDPR'],
  education: ['GDPR', 'ISO 27001'],
  technology: ['ISO 27001', 'GDPR', 'NIS2'],
  manufacturing: ['NIS2', 'ISO 27001'],
  retail: ['GDPR', 'ISO 27001'],
  energy: ['NIS2', 'DORA', 'ISO 27001'],
  telecommunications: ['NIS2', 'ISO 27001', 'GDPR'],
  professional_services: ['GDPR', 'ISO 27001'],
  logistics: ['NIS2', 'GDPR'],
  other: [],
};

export const FRAMEWORKS: FrameworkDefinition[] = [
  { key: 'NIS2', name: 'NIS2', color: 'blue' },
  { key: 'DORA', name: 'DORA', color: 'purple' },
  { key: 'ISO 27001', name: 'ISO 27001', color: 'green' },
  { key: 'GDPR', name: 'GDPR', color: 'amber' },
];
