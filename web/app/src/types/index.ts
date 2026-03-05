// Auth
export type UserRole = 'super_admin' | 'admin' | 'procurement_manager' | 'technician' | 'employee';

export interface CompanyMembership {
  company_id: string;
  company_name: string;
  slug: string;
  role: UserRole;
  is_current: boolean;
}

export interface User {
  id: string;
  email: string;
  name?: string | null;
  role: UserRole;
  company_id: string | null;
  company_name?: string | null;
  department_id: string | null;
  employee_role_id?: string | null;
  is_active: boolean;
  password_set?: boolean;
  has_oauth?: boolean;
  hidden_nav_items?: Record<string, string[]> | null;
  needs_onboarding?: boolean;
  company_plan?: string | null;
  demo_days_remaining?: number | null;
  street_line_1?: string | null;
  street_line_2?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  country?: string | null;
  created_at: string;
}

// Pagination
export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface SingleResponse<T> {
  data: T;
}

// Company
export type CompanyStatus = 'active' | 'suspended' | 'deactivated';

export interface Company {
  id: string;
  name: string;
  status: CompanyStatus;
  email_domains: string[];
  is_active: boolean;
  plan?: string;
  billing_status?: string;
  user_count?: number;
  asset_count?: number;
  department_count?: number;
  trial_days_remaining?: number | null;
  created_at: string;
}

export interface CompanySettings {
  id: string;
  name: string;
  slug: string;
  auth_mode: string;
  email_domains: string[];
  sector?: string | null;
}

// Department
export interface Department {
  id: string;
  name: string;
  company_id: string;
  is_active: boolean;
  manager_user_id?: string | null;
  manager_email?: string | null;
  manager_name?: string | null;
  priority_weight?: number;
  budget_enforcement_enabled?: boolean;
  user_count?: number;
  created_at: string;
}

// Asset
export type AssetStatus = 'in_stock' | 'assigned' | 'in_repair' | 'decommissioned';

export interface AssetTypeDefinition {
  id: string;
  code: string;
  name: string;
  icon: string | null;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface Asset {
  id: string;
  company_id: string;
  type: string;
  brand: string;
  model: string;
  serial_number: string;
  status: AssetStatus;
  assigned_to: string | null;
  assigned_to_email?: string | null;
  department_id: string | null;
  location_id: string | null;
  location_name?: string | null;
  purchase_date: string | null;
  warranty_expiration: string | null;
  notes: string | null;
  custom_fields?: CustomFieldValue[] | null;
  criticality: string | null;
  impact_score: number | null;
  rto_minutes: number | null;
  rpo_minutes: number | null;
  bia_justification: string | null;
  bia_reviewed_at: string | null;
  bia_reviewed_by: string | null;
  created_at: string;
  updated_at: string;
}

export type AssetCriticality = 'critical' | 'high' | 'medium' | 'low';

export interface AssetLocation {
  id: string;
  name: string;
  is_system: boolean;
  system_key: string | null;
  in_use: boolean;
  street_line_1?: string | null;
  street_line_2?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  country?: string | null;
  phone?: string | null;
  is_personal: boolean;
  user_id?: string | null;
  asset_count: number;
  created_at: string;
}

export interface AssetEvent {
  id: string;
  asset_id: string;
  event_type: string;
  data: Record<string, unknown>;
  performed_by: string;
  performed_by_email?: string | null;
  created_at: string;
}

export interface AssignableUser {
  id: string;
  email: string;
  name?: string | null;
}

// Request
export type RequestType = 'incident' | 'new_equipment' | 'onboarding' | 'repair' | 'configuration' | 'access_request';
export type RequestStatus = 'pending_approval' | 'submitted' | 'in_review' | 'in_progress' | 'waiting_for_employee' | 'resolved' | 'rejected';
export type RequestPriority = 'low' | 'medium' | 'high' | 'urgent';
export type RequestSubtype =
  | 'hardware' | 'software' | 'network' | 'security' | 'other'
  | 'computer' | 'mobile' | 'peripheral' | 'monitor' | 'software_license'
  | 'software_install' | 'account_setup' | 'permissions'
  | 'system_access' | 'physical_access' | 'vpn';

export const VALID_SUBTYPES: Record<RequestType, RequestSubtype[]> = {
  incident: [],
  new_equipment: ['computer', 'mobile', 'peripheral', 'monitor', 'software_license'],
  onboarding: [],
  repair: ['hardware', 'software', 'network', 'security', 'other'],
  configuration: ['software_install', 'account_setup', 'permissions'],
  access_request: ['system_access', 'physical_access', 'vpn'],
};

export interface ServiceRequest {
  id: string;
  company_id: string;
  created_by: string;
  created_by_name?: string | null;
  created_by_email?: string | null;
  assigned_to: string | null;
  assigned_to_name?: string | null;
  assigned_to_email?: string | null;
  type: RequestType;
  subtype?: string | null;
  title: string;
  description: string;
  status: RequestStatus;
  priority: RequestPriority;
  data: Record<string, unknown>;
  resolved_at: string | null;
  comment_count?: number;
  custom_fields?: CustomFieldValue[] | null;
  workflow_template_id?: string | null;
  workflow_template_name?: string | null;
  workflow_template_icon?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: string;
  request_id: string;
  author_id: string;
  author_email?: string | null;
  author_name?: string | null;
  author_role?: string | null;
  body: string;
  created_at: string;
}

export interface Note {
  id: string;
  request_id: string;
  author_id: string;
  author_email?: string | null;
  author_name?: string | null;
  author_role?: string | null;
  body: string;
  created_at: string;
}

export interface RequestEventItem {
  id: string;
  request_id: string;
  event_type: string;
  data?: Record<string, unknown> | null;
  performed_by: string;
  performed_by_name?: string | null;
  performed_by_email?: string | null;
  created_at?: string | null;
}

// Notification
export interface Notification {
  id: string;
  user_id: string;
  event_type: string;
  title: string;
  body: string;
  data: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
}

// Dashboard
export interface RequestSummary {
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  total_open: number;
  total_resolved: number;
}

export interface ResolutionTime {
  avg_hours: number | null;
  by_technician: { technician_id: string; avg_hours: number; resolved_count: number }[];
}

export interface TrendBucket {
  period: string;
  total: number;
  by_type: Record<string, number>;
}

export interface AssetSummary {
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  total: number;
}

export interface WarrantyAlert {
  id: string;
  brand: string;
  model: string;
  serial_number: string;
  warranty_expiration: string;
  days_remaining: number;
  assigned_to: string | null;
}

export interface AgingAlert {
  id: string;
  brand: string;
  model: string;
  serial_number: string;
  purchase_date: string;
  age_years: number;
  assigned_to: string | null;
}

export interface SlaAlert {
  id: string;
  title: string;
  type: string;
  priority: string;
  status: string;
  assigned_to: string | null;
  created_at: string;
  hours_open: number;
  sla_threshold_hours: number;
  breached: boolean;
}

// API Key
export interface ApiKey {
  id: string;
  name: string;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
}

export interface CreatedApiKey {
  id: string;
  name: string;
  raw_key: string;
  created_at: string;
  is_active: boolean;
}

// Equipment Profile
export interface EquipmentProfileItem {
  id: string;
  asset_type: string;
  quantity: number;
  preferred_brand?: string | null;
  preferred_model?: string | null;
  min_ram_gb?: number | null;
  min_storage_gb?: number | null;
  budget_cents?: number | null;
}

export interface EquipmentProfile {
  id: string;
  company_id: string;
  department_id: string;
  employee_role_id: string;
  is_active: boolean;
  items: EquipmentProfileItem[];
  created_at: string | null;
  updated_at: string | null;
}

// Employee Role
export interface EmployeeRole {
  id: string;
  company_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

// Assignment AI Config
export type AIProvider = 'openai' | 'groq';

export interface CompanyAIConfig {
  id: string;
  company_id: string;
  provider: string;
  prompt_template: string;
  model?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

// Classification Config
export interface CompanyClassificationConfig {
  id: string;
  company_id: string;
  is_enabled: boolean;
  provider: string;
  model?: string | null;
  confidence_threshold: number;
  prompt_template?: string | null;
  timeout_seconds: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AIClassificationData {
  ai_used: boolean;
  provider?: string;
  model?: string;
  confidence?: number;
  suggested_type?: string;
  suggested_subtype?: string | null;
  priority_hint?: number;
  override_applied?: boolean;
  user_original?: { type: string; subtype?: string | null };
  latency_ms?: number;
}

// Vendor
export type VendorCategory = 'hardware' | 'software' | 'saas' | 'consulting' | 'telecom' | 'cloud' | 'managed_services' | 'other';
export type VendorRiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type ContractType = 'service' | 'supply' | 'licensing' | 'saas';
export type ContractStatus = 'draft' | 'active' | 'expired' | 'terminated';

export interface Vendor {
  id: string;
  company_id: string;
  name: string;
  contact_email?: string | null;
  phone?: string | null;
  address?: string | null;
  notes?: string | null;
  is_active: boolean;
  is_critical_ict: boolean;
  risk_level?: VendorRiskLevel | null;
  website?: string | null;
  category?: VendorCategory | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface VendorContract {
  id: string;
  vendor_id: string;
  company_id: string;
  contract_type: ContractType;
  title: string;
  start_date: string;
  end_date?: string | null;
  renewal_date?: string | null;
  auto_renewal: boolean;
  annual_value?: string | null;
  currency?: string | null;
  security_clauses: Record<string, boolean>;
  notes?: string | null;
  status: ContractStatus;
  document_count?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface VendorContractDocument {
  id: string;
  contract_id: string;
  company_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_by: string;
  created_at?: string | null;
}

export interface VendorRiskAssessment {
  id: string;
  vendor_id: string;
  company_id: string;
  assessed_by: string;
  assessment_date: string;
  next_review_date?: string | null;
  data_handling_score: number;
  security_certs_score: number;
  incident_response_score: number;
  business_continuity_score: number;
  subcontractor_score: number;
  overall_risk_level: VendorRiskLevel;
  justification?: string | null;
  created_at?: string | null;
}

export type BusinessFunction =
  | 'it_operations'
  | 'security'
  | 'communications'
  | 'data_storage'
  | 'cloud_infrastructure'
  | 'software'
  | 'hardware_supply'
  | 'consulting'
  | 'other';

export interface VendorDependency {
  id: string;
  vendor_id: string;
  company_id: string;
  service_description: string;
  business_function: BusinessFunction;
  is_critical: boolean;
  notes?: string | null;
  created_at?: string | null;
}

export interface ConcentrationRiskItem {
  vendor_id: string;
  vendor_name: string;
  critical_count: number;
  total_critical: number;
  percentage: number;
  is_above_threshold: boolean;
}

// Vendor Risk Profile
export interface VendorLatestAssessment {
  id: string;
  assessment_date: string;
  next_review_date?: string | null;
  data_handling_score: number;
  security_certs_score: number;
  incident_response_score: number;
  business_continuity_score: number;
  subcontractor_score: number;
  overall_risk_level: string;
  justification?: string | null;
}

export interface VendorIncidentSummary {
  id: string;
  title: string;
  severity: string;
  status: string;
  created_at?: string | null;
}

export interface VendorRiskSummary {
  id: string;
  title: string;
  risk_level?: string | null;
  status: string;
}

export interface VendorRiskProfile {
  id: string;
  name: string;
  contact_email?: string | null;
  phone?: string | null;
  address?: string | null;
  website?: string | null;
  category?: string | null;
  is_critical_ict: boolean;
  risk_level?: string | null;
  is_active: boolean;
  latest_assessment?: VendorLatestAssessment | null;
  active_contracts_count: number;
  total_contracts_count: number;
  dependency_count: number;
  critical_dependency_count: number;
  incident_count: number;
  risk_count: number;
  incidents: VendorIncidentSummary[];
  risks: VendorRiskSummary[];
}

// Procurement Config
export type EnforcementMode = 'warn' | 'strict';

export interface CompanyProcurementConfig {
  id?: string | null;
  company_id: string;
  enforcement_mode: EnforcementMode;
  approval_threshold_cents: number;
  po_number_prefix: string;
  fiscal_year_start_month: number;
  currency: string;
  auto_create_assets: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

// Purchase Order
export type PurchaseOrderStatus =
  | 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'ORDERED'
  | 'PARTIALLY_RECEIVED' | 'RECEIVED' | 'CLOSED' | 'CANCELLED';

export interface PurchaseOrderItem {
  id: string;
  description: string;
  asset_type?: string | null;
  quantity: number;
  unit_cost_cents: number;
  total_cost_cents: number;
  received_quantity: number;
  received_at?: string | null;
  linked_asset_id?: string | null;
  notes?: string | null;
}

export interface PurchaseOrder {
  id: string;
  company_id: string;
  po_number: string;
  vendor_id?: string | null;
  vendor_name: string;
  department_id: string;
  status: PurchaseOrderStatus;
  total_amount_cents: number;
  currency: string;
  notes?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  ordered_at?: string | null;
  cancellation_reason?: string | null;
  created_by: string;
  items: PurchaseOrderItem[];
  request_ids: string[];
  created_at?: string | null;
  updated_at?: string | null;
}

// Report
export type ReportType = 'asset_inventory' | 'request_summary' | 'technician_performance' | 'department_spending';
export type ReportStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Report {
  id: string;
  type: ReportType;
  status: ReportStatus;
  parameters: Record<string, unknown> | null;
  created_at: string;
  completed_at: string | null;
  error_message?: string | null;
}

// Dashboard — Budget Health
export interface AtRiskDepartment {
  department_id: string;
  department_name: string;
  utilization_pct: number;
  remaining_cents: number;
}

export interface BudgetHealth {
  total_allocated_cents: number;
  total_spent_cents: number;
  departments_at_risk: AtRiskDepartment[];
}

// Appointment
export type AppointmentStatus = 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW';

export interface Appointment {
  id: string;
  company_id: string;
  request_id: string;
  technician_id: string;
  employee_id: string;
  status: AppointmentStatus;
  scheduled_start: string;
  scheduled_end: string;
  duration_minutes: number;
  location?: string | null;
  notes?: string | null;
  cancellation_reason?: string | null;
  cancelled_by?: string | null;
  rescheduled_from_id?: string | null;
  completed_at?: string | null;
  created_by: string;
  created_at?: string | null;
  updated_at?: string | null;
  technician_name?: string | null;
  technician_email?: string | null;
  employee_name?: string | null;
  employee_email?: string | null;
}

export interface AvailabilityWindow {
  id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

export interface AvailabilityOverrideItem {
  id: string;
  date: string;
  is_available: boolean;
  start_time?: string | null;
  end_time?: string | null;
  reason?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface TimeSlot {
  start: string;
  end: string;
}

// Dashboard — Recent POs
export interface RecentPO {
  id: string;
  po_number: string;
  vendor_name: string;
  status: string;
  total_amount_cents: number;
  created_at?: string | null;
}

// Shipment
export type ShipmentStatus = 'draft' | 'dispatched' | 'in_transit' | 'delivered' | 'failed' | 'cancelled';
export type ShipmentDirection = 'outbound' | 'inbound';
export type DestinationType = 'employee_home' | 'office' | 'vendor';

export interface ShipmentItem {
  id: string;
  shipment_id: string;
  asset_id: string;
  notes?: string | null;
}

export interface Shipment {
  id: string;
  company_id: string;
  direction: ShipmentDirection;
  destination_type: DestinationType;
  status: ShipmentStatus;
  origin_location_id?: string | null;
  destination_location_id?: string | null;
  carrier?: string | null;
  service_level?: string | null;
  tracking_number?: string | null;
  tracking_url?: string | null;
  items_description?: string | null;
  internal_notes?: string | null;
  recipient_name?: string | null;
  recipient_user_id?: string | null;
  request_id?: string | null;
  po_id?: string | null;
  return_for_shipment_id?: string | null;
  notes?: string | null;
  failure_reason?: string | null;
  cancellation_reason?: string | null;
  items: ShipmentItem[];
  item_count: number;
  dispatched_at?: string | null;
  delivered_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

// Shipping Address
export interface ShippingAddress {
  id: string;
  company_id: string;
  label: string;
  street_line_1: string;
  street_line_2?: string | null;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  recipient_name?: string | null;
  phone?: string | null;
  user_id?: string | null;
  is_office: boolean;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

// Dashboard — Shipments
export interface ShipmentDashboard {
  active_by_status: Record<string, number>;
  recent_deliveries: number;
  failed_count: number;
}

// Maintenance
export type MaintenanceStatus =
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'SKIPPED';
export type MaintenancePriority =
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'
  | 'CRITICAL';
export type RecurrenceFrequency =
  | 'DAILY'
  | 'WEEKLY'
  | 'MONTHLY'
  | 'QUARTERLY'
  | 'YEARLY';

export interface MaintenanceRecord {
  id: string;
  company_id: string;
  asset_id: string;
  status: MaintenanceStatus;
  priority: MaintenancePriority;
  title: string;
  description?: string | null;
  technician_id?: string | null;
  template_id?: string | null;
  plan_id?: string | null;
  checklist_items: string[];
  scheduled_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  completion_notes?: string | null;
  actual_findings?: string | null;
  cancellation_reason?: string | null;
  skip_reason?: string | null;
  reminder_48h_sent: boolean;
  overdue_alert_sent: boolean;
  created_at?: string | null;
  updated_at?: string | null;
  employee_name?: string | null;
  employee_email?: string | null;
}

export interface MaintenanceChecklistItem {
  title: string;
  description?: string | null;
  is_required: boolean;
}

export interface MaintenanceTemplate {
  id: string;
  company_id: string;
  name: string;
  default_priority: MaintenancePriority;
  description?: string | null;
  recurrence_frequency?: RecurrenceFrequency | null;
  recurrence_interval: number;
  asset_type_filter?: string | null;
  checklist_items: MaintenanceChecklistItem[];
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MaintenancePlan {
  id: string;
  company_id: string;
  template_id: string;
  asset_id: string;
  is_active: boolean;
  next_due_at: string;
  last_generated_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MaintenanceDashboard {
  scheduled: number;
  overdue: number;
  in_progress: number;
  completed_30d: number;
}

// User Import
export interface ImportRowError {
  row: number;
  error: string;
}

export interface ImportDepartment {
  id: string;
  name: string;
}

export interface ImportPreviewResult {
  total_rows: number;
  valid_rows: number;
  new_users: number;
  existing_users: number;
  errors: ImportRowError[];
  unknown_departments: string[];
  existing_departments: ImportDepartment[];
  unknown_employee_roles: string[];
  existing_employee_roles: ImportDepartment[];
}

export interface ImportConfirmResult {
  total: number;
  successful: number;
  updated: number;
  failed: ImportRowError[];
  departments_created: string[];
  employee_roles_created: string[];
  invitations_sent: number;
}

// Security Incident
export type IncidentType = 'phishing' | 'malware' | 'ransomware' | 'data_breach' | 'unauthorized_access' | 'ddos' | 'social_engineering' | 'insider_threat' | 'other';
export type IncidentSeverity = 'P1' | 'P2' | 'P3' | 'P4';
export type IncidentStatus = 'detected' | 'triaged' | 'contained' | 'eradicated' | 'recovered' | 'closed';

export interface IncidentTimelineEntry {
  id: string;
  event_type: string;
  description: string;
  actor_id: string;
  actor_name?: string | null;
  created_at?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface IncidentListItem {
  id: string;
  title: string;
  incident_type: IncidentType;
  severity: IncidentSeverity;
  status: IncidentStatus;
  assigned_to?: string | null;
  assigned_to_name?: string | null;
  detected_at?: string | null;
  custom_fields?: CustomFieldValue[] | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface IncidentDetail {
  id: string;
  title: string;
  description: string;
  incident_type: IncidentType;
  severity: IncidentSeverity;
  status: IncidentStatus;
  attack_vector?: string | null;
  data_breach_scope?: string | null;
  reported_by: string;
  reported_by_name?: string | null;
  assigned_to?: string | null;
  assigned_to_name?: string | null;
  detected_at?: string | null;
  close_reason?: string | null;
  closed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  timeline: IncidentTimelineEntry[];
  reports: RegulatoryReport[];
  assets: IncidentAsset[];
  vendors: IncidentVendor[];
  postmortem?: PostMortem | null;
  custom_fields?: CustomFieldValue[] | null;
}

export interface PostMortem {
  id: string;
  root_cause: string;
  lessons_learned: string;
  corrective_actions: string;
  created_by_name?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MyIncident {
  id: string;
  title: string;
  incident_type: string;
  severity: string;
  status: string;
  created_at?: string | null;
}

export interface UpcomingDeadline {
  incident_id: string;
  incident_title: string;
  report_type: string;
  deadline_at: string;
  time_remaining_seconds: number;
}

export interface RecentIncident {
  id: string;
  title: string;
  incident_type: string;
  severity: string;
  status: string;
  detected_at?: string | null;
  created_at?: string | null;
}

export interface IncidentDashboard {
  total_active: number;
  total_closed: number;
  active_by_severity: Record<string, number>;
  by_type: Record<string, number>;
  mttc_hours: number | null;
  mttr_hours: number | null;
  upcoming_deadlines: UpcomingDeadline[];
  recent_incidents: RecentIncident[];
}

export interface IncidentAsset {
  asset_id: string;
  asset_name: string;
  asset_type?: string | null;
  impact_description?: string | null;
}

export interface IncidentVendor {
  vendor_id: string;
  vendor_name: string;
  involvement_description?: string | null;
}

export interface RegulatoryReport {
  id: string;
  report_type: string;
  status: string;
  deadline_at?: string | null;
  generated_at?: string | null;
  submitted_at?: string | null;
  time_remaining_seconds?: number | null;
  elapsed_percentage?: number | null;
}

// Risk Register
export interface RiskListItem {
  id: string;
  title: string;
  category: string;
  status: string;
  risk_level?: string | null;
  likelihood?: number | null;
  impact?: number | null;
  treatment?: string | null;
  owner_id?: string | null;
  owner_name?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface MitigationPlan {
  id: string;
  description: string;
  status: string;
  owner_id?: string | null;
  owner_name?: string | null;
  target_date?: string | null;
  created_at?: string | null;
}

export interface RiskLink {
  id: string;
  link_type: string;
  link_id: string;
  link_name?: string | null;
}

export interface RiskHistoryEntry {
  id: string;
  event_type: string;
  description: string;
  actor_id: string;
  actor_name?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at?: string | null;
}

export interface RiskDetail {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  likelihood?: number | null;
  impact?: number | null;
  risk_level?: string | null;
  treatment?: string | null;
  review_cadence?: string | null;
  next_review_at?: string | null;
  owner_id?: string | null;
  owner_name?: string | null;
  created_by: string;
  created_by_name?: string | null;
  mitigations: MitigationPlan[];
  links: RiskLink[];
  history: RiskHistoryEntry[];
  created_at?: string | null;
  updated_at?: string | null;
}

// Audit Trail
export interface AuditEntry {
  id: string;
  actor_email: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  http_method: string;
  response_status: number;
  ip_address: string | null;
  tag_count: number;
  created_at: string;
}

export interface AuditTag {
  id: string;
  control_id: string;
  control_code: string;
  control_name: string;
  framework: string;
  tagged_by: string;
  tagged_at: string | null;
}

export interface AuditEntryDetail {
  id: string;
  actor_id: string | null;
  actor_email: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  http_method: string;
  http_path: string;
  response_status: number;
  ip_address: string | null;
  user_agent: string | null;
  request_data: Record<string, unknown> | null;
  response_summary: Record<string, unknown> | null;
  hash: string;
  tags: AuditTag[];
  created_at: string;
}

export interface ComplianceControl {
  id: string;
  code: string;
  name: string;
  framework: string;
  description: string | null;
  is_predefined: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AuditExportStatus {
  task_id: string;
  status: string;
  download_url: string | null;
}

export interface GdprRequest {
  id: string;
  target_user_email: string;
  request_type: string;
  status: string;
  reason: string | null;
  error_message: string | null;
  download_url: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

// Compliance Dashboard
export type ComplianceStatusType = 'compliant' | 'partial' | 'non_compliant' | 'not_assessed';
export type EvidenceTypeValue = 'audit_log' | 'incident' | 'risk' | 'sla' | 'manual';

export interface ControlAssessment {
  control_id: string;
  control_code: string;
  control_name: string;
  framework: string;
  description: string | null;
  is_predefined: boolean;
  status: ComplianceStatusType;
  notes: string | null;
  assessed_by: string | null;
  assessed_at: string | null;
  evidence_count: number;
}

export interface ComplianceEvidence {
  id: string;
  control_id: string;
  evidence_type: EvidenceTypeValue;
  reference_id: string | null;
  title: string;
  description: string | null;
  url: string | null;
  added_by: string;
  created_at: string | null;
}

export interface FrameworkSummary {
  framework: string;
  total_controls: number;
  compliant: number;
  partial: number;
  non_compliant: number;
  not_assessed: number;
  compliance_pct: number;
  evidence_coverage_pct: number;
}

export interface ComplianceDashboard {
  overall_compliance_pct: number;
  total_controls: number;
  compliant: number;
  partial: number;
  non_compliant: number;
  not_assessed: number;
  controls_with_evidence: number;
  controls_without_evidence: number;
  frameworks: FrameworkSummary[];
  gap_controls: ControlAssessment[];
}

// Custom Fields
export type CustomFieldType = 'text' | 'number' | 'date' | 'select' | 'multi_select' | 'boolean' | 'file';

export interface CustomFieldFile {
  id: string;
  name: string;
  size: number;
  mime: string;
  key: string;
  download_path?: string;
}

export interface CustomFieldDefinition {
  id: string;
  entity_type: 'asset' | 'request' | 'incident';
  field_key: string;
  label: string;
  description: string | null;
  field_type: CustomFieldType;
  options: string[] | null;
  required: boolean;
  sort_order: number;
  is_active: boolean;
  visible_to_employees: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface CustomFieldValue {
  key: string;
  label: string;
  type: CustomFieldType;
  value: unknown;
  required: boolean;
  is_active: boolean;
  visible_to_employees: boolean;
  options?: string[];
}

// Knowledge Base
export interface ArticleListItem {
  id: string;
  title: string;
  slug: string;
  excerpt?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  status: string;
  author_id: string;
  author_name?: string | null;
  view_count: number;
  published_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ArticleDetail {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  status: string;
  author_id: string;
  author_name?: string | null;
  view_count: number;
  published_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ArticleCategory {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  sort_order: number;
  article_count: number;
}

export interface ArticleVersion {
  id: string;
  version_number: number;
  title: string;
  content: string;
  edited_by: string;
  editor_name?: string | null;
  created_at?: string | null;
}

// Workflow Templates
export interface WorkflowSubtype {
  id: string;
  name: string;
  description?: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface ChecklistItemDefinition {
  id: string;
  title: string;
  description?: string | null;
  assignee_role?: string | null;
  sort_order: number;
  is_required: boolean;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description?: string | null;
  icon?: string | null;
  is_active: boolean;
  require_all_complete: boolean;
  sort_order: number;
  subtypes: WorkflowSubtype[];
  checklist_items: ChecklistItemDefinition[];
  created_at?: string | null;
  updated_at?: string | null;
}

// Asset Checkout / Custody
export type CheckoutStatus = 'open' | 'accepted' | 'checked_in' | 'cancelled';

export interface AssetCheckout {
  id: string;
  asset_id: string;
  user_id: string;
  checked_out_by: string;
  checked_out_at: string;
  condition_out: string;
  condition_out_notes?: string | null;
  notes_out?: string | null;
  accepted_at?: string | null;
  checked_in_at?: string | null;
  checked_in_by?: string | null;
  condition_in?: string | null;
  condition_in_notes?: string | null;
  notes_in?: string | null;
  cancelled_at?: string | null;
  cancelled_by?: string | null;
  cancel_reason?: string | null;
  maintenance_id?: string | null;
  auto_assigned: boolean;
  status: CheckoutStatus;
  created_at?: string | null;
}

export interface MyCustody {
  pending_acceptance: MyCustodyItem[];
  open: MyCustodyItem[];
}

export interface MyCustodyItem {
  checkout_id: string;
  asset_id: string;
  condition_out: string;
  checked_out_at: string;
  accepted_at?: string | null;
  status: string;
}

export interface MyCustodyHistoryItem {
  checkout_id: string;
  asset_id: string;
  asset_type?: string | null;
  asset_brand?: string | null;
  asset_model?: string | null;
  condition_out: string;
  condition_in?: string | null;
  checked_out_at: string;
  checked_in_at?: string | null;
  cancelled_at?: string | null;
  status: string;
}

// Request Checklist
export interface RequestChecklistItem {
  id: string;
  request_id: string;
  title: string;
  description?: string | null;
  assignee_id?: string | null;
  is_required: boolean;
  is_completed: boolean;
  completed_by?: string | null;
  completed_at?: string | null;
  sort_order: number;
  created_at?: string | null;
}

export interface ChecklistProgress {
  total: number;
  completed: number;
  required_remaining: number;
}

// CI Relationships
export interface CIRelationship {
  id: string;
  source_asset_id: string;
  target_asset_id: string;
  relationship_type: string;
  description: string | null;
  created_at: string;
  created_by: string;
  target_asset_name: string | null;
  target_asset_serial: string | null;
  target_asset_type: string | null;
  target_asset_criticality: string | null;
  target_asset_status: string | null;
  source_asset_name: string | null;
  source_asset_serial: string | null;
  source_asset_type: string | null;
  source_asset_criticality: string | null;
  source_asset_status: string | null;
}

// Affected Assets
export interface RequesterAsset {
  id: string;
  brand: string;
  model: string;
  serial_number: string;
  type: string;
  criticality: string | null;
  status: string;
  is_affected: boolean;
}

// Vulnerability
export interface Vulnerability {
  id: string;
  cve_id?: string | null;
  title: string;
  description?: string | null;
  source: string;
  cvss_score?: number | null;
  severity: string;
  status: string;
  affected_software?: string | null;
  affected_versions?: string | null;
  published_at?: string | null;
  discovered_at?: string | null;
  remediation_notes?: string | null;
  vendor_id?: string | null;
  created_by: string;
  created_by_name?: string | null;
  created_at?: string;
  updated_at?: string | null;
}

export interface VulnerabilityEvent {
  id: string;
  event_type: string;
  data?: Record<string, unknown> | null;
  performed_by: string;
  performed_by_name?: string | null;
  created_at?: string;
}

export interface VulnerabilityAsset {
  id: string;
  asset_id: string;
  asset_name?: string | null;
  asset_tag?: string | null;
  asset_criticality?: string | null;
  status: string;
  notes?: string | null;
  remediation_request_id?: string | null;
  patched_at?: string | null;
  patched_by?: string | null;
  patched_by_name?: string | null;
  created_at?: string | null;
}

export interface VulnerabilityDetail extends Vulnerability {
  events: VulnerabilityEvent[];
  affected_assets: VulnerabilityAsset[];
  all_assets_remediated: boolean;
}

// CMDB Dashboard
export interface ImpactAsset {
  id: string;
  name: string;
  asset_tag: string | null;
  criticality: string | null;
  depth: number;
  relationship_type: string;
}

export interface ImpactRadius {
  critical: number;
  high: number;
  medium: number;
  low: number;
  unclassified: number;
  total: number;
}

export interface AssetImpact {
  asset_id: string;
  upstream: ImpactAsset[];
  downstream: ImpactAsset[];
  radius: ImpactRadius;
}

export interface MostDependedAsset {
  asset_id: string;
  asset_name: string;
  asset_tag: string | null;
  incoming_count: number;
}

export interface OverdueBIAReview {
  asset_id: string;
  asset_name: string;
  asset_tag: string | null;
  criticality: string;
  bia_reviewed_at: string | null;
}

export interface CMDBDashboard {
  criticality_distribution: Record<string, number>;
  orphan_critical_count: number;
  bia_total_critical_high: number;
  bia_has_coverage: number;
  bia_coverage_pct: number;
  total_relationships: number;
  relationships_by_type: Record<string, number>;
  most_depended_upon: MostDependedAsset[];
  overdue_bia_reviews: OverdueBIAReview[];
}

// Post-Implementation Review
export interface PIR {
  id: string;
  outcome: string;
  issues_found: string | null;
  lessons_learned: string | null;
  follow_up_actions: string | null;
  created_by: string;
  created_by_name: string | null;
  created_at: string | null;
}

// Change Management
export interface ChangeRequest {
  id: string;
  title: string;
  change_type: string;
  status: string;
  planned_date: string | null;
  assigned_to: string | null;
  assigned_to_name: string | null;
  requested_by: string;
  requested_by_name: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ChangeEvent {
  id: string;
  event_type: string;
  description: string;
  actor_id: string;
  actor_name: string | null;
  created_at: string | null;
  metadata: Record<string, unknown> | null;
}

export interface ChangeAsset {
  id: string;
  asset_id: string;
  asset_name: string | null;
  asset_tag: string | null;
  asset_brand: string | null;
  asset_model: string | null;
  created_at: string | null;
}

export interface ChangeRequestDetail {
  id: string;
  company_id: string;
  title: string;
  description: string | null;
  change_type: string;
  status: string;
  business_justification: string | null;
  risk_assessment: string | null;
  rollback_plan: string | null;
  planned_date: string | null;
  requested_by: string;
  requested_by_name: string | null;
  assigned_to: string | null;
  assigned_to_name: string | null;
  approved_by: string | null;
  approved_by_name: string | null;
  approved_at: string | null;
  rejected_by: string | null;
  rejected_by_name: string | null;
  rejected_at: string | null;
  rejection_reason: string | null;
  started_at: string | null;
  implemented_at: string | null;
  implementation_notes: string | null;
  rolled_back_at: string | null;
  rollback_reason: string | null;
  closed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  timeline: ChangeEvent[];
  affected_assets: ChangeAsset[];
  pir: PIR | null;
}

// Change Dashboard
export interface UpcomingChange {
  id: string;
  title: string;
  change_type: string;
  planned_date: string | null;
  assigned_to: string | null;
  assigned_to_name: string | null;
}

export interface RecentImplemented {
  id: string;
  title: string;
  change_type: string;
  implemented_at: string | null;
  pir_outcome: string | null;
}

export interface ChangeDashboard {
  total_open: number;
  pending_approval: number;
  in_progress: number;
  implemented: number;
  scheduled_this_week: number;
  status_counts: Record<string, number>;
  type_counts: Record<string, number>;
  upcoming_scheduled: UpcomingChange[];
  recently_implemented: RecentImplemented[];
  rolled_back_90_days: number;
}

// Reseller
export type ResellerStatus = 'pending' | 'active' | 'suspended' | 'deactivated';

export interface Reseller {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  company_name: string | null;
  tax_id: string | null;
  commission_pct: number;
  min_payout_cents: number;
  referral_code: string;
  status: ResellerStatus;
  created_at: string;
  updated_at: string | null;
}

export interface ResellerDashboard {
  reseller_id: string;
  name: string;
  referral_code: string;
  status: string;
  client_count: number;
  total_commissions_cents: number;
  available_balance_cents: number;
  pending_payout_cents: number;
}
