// Auth
export type UserRole = 'super_admin' | 'admin' | 'technician' | 'employee';

export interface User {
  id: string;
  email: string;
  name?: string | null;
  role: UserRole;
  company_id: string | null;
  department_id: string | null;
  is_active: boolean;
  password_set?: boolean;
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
  user_count?: number;
  department_count?: number;
  created_at: string;
}

// Department
export interface Department {
  id: string;
  name: string;
  company_id: string;
  is_active: boolean;
  user_count?: number;
  created_at: string;
}

// Asset
export type AssetType = 'laptop' | 'desktop' | 'phone' | 'tablet' | 'monitor' | 'printer' | 'other';
export type AssetStatus = 'in_stock' | 'assigned' | 'in_repair' | 'decommissioned';

export interface Asset {
  id: string;
  company_id: string;
  type: AssetType;
  brand: string;
  model: string;
  serial_number: string;
  status: AssetStatus;
  assigned_to: string | null;
  assigned_to_email?: string | null;
  department_id: string | null;
  purchase_date: string | null;
  warranty_expiration: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
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
export type RequestType = 'incident' | 'new_equipment' | 'onboarding';
export type RequestStatus = 'submitted' | 'in_review' | 'in_progress' | 'resolved' | 'rejected';
export type RequestPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface ServiceRequest {
  id: string;
  company_id: string;
  created_by: string;
  created_by_email?: string | null;
  assigned_to: string | null;
  assigned_to_email?: string | null;
  type: RequestType;
  title: string;
  description: string;
  status: RequestStatus;
  priority: RequestPriority;
  data: Record<string, unknown>;
  resolved_at: string | null;
  comment_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: string;
  request_id: string;
  author_id: string;
  author_email?: string | null;
  body: string;
  created_at: string;
}

export interface Note {
  id: string;
  request_id: string;
  author_id: string;
  author_email?: string | null;
  body: string;
  created_at: string;
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

// Report
export type ReportType = 'asset_inventory' | 'request_summary' | 'technician_performance';
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
