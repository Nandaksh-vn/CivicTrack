import type { ComplaintStatus, UserRole } from "@/lib/status";

export interface DepartmentRef {
  id: number;
  name: string;
  code: string;
}
export interface CategoryRef {
  id: number;
  name: string;
  code: string;
}
export interface User {
  id: number;
  full_name: string;
  email: string;
  phone: string | null;
  role: UserRole;
  department: DepartmentRef | null;
  is_active: boolean;
}
export interface TokenResponse {
  token: string;
  token_type: string;
  expires_in: number;
  user: User;
}
export interface ImageMeta {
  id: number;
  kind: string;
  mime_type: string;
  size_bytes: number;
  url: string;
}
export interface ComplaintSummary {
  id: number;
  complaint_number: string;
  title: string;
  status: ComplaintStatus;
  category: string;
  department: string;
  submitted_at: string;
  accepted_at?: string | null;
  resolution_due_at?: string | null;
  overdue?: boolean;
  is_overdue?: boolean;
  overdue_seconds?: number | null;
  assigned_to?: { id: number; full_name: string } | null;
}
export interface ComplaintDetail extends ComplaintSummary {
  description: string;
  priority: string;
  category_ref?: CategoryRef;
  department_ref?: DepartmentRef;
  location?: { text: string | null; latitude: number | null; longitude: number | null };
  images: ImageMeta[];
  escalated_at?: string | null;
  resolved_at?: string | null;
  resolution_note?: string | null;
  resolution?: {
    note: string | null;
    resolved_at: string | null;
    resolved_by: { id: number; full_name: string } | null;
    evidence: ImageMeta[];
  } | null;
  timeline_url?: string;
}
export interface TimelineActor {
  id: number | null;
  display_name: string;
  role: string;
}
export interface TimelineEvent {
  id: string;
  event_type: string;
  from_status: string | null;
  to_status: string | null;
  actor: TimelineActor;
  note: string | null;
  created_at: string;
  action_type?: string | null;
  image?: ImageMeta | null;
  overdue_seconds?: number | null;
}
export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}
export interface NotificationItem {
  id: number;
  trigger_code: string;
  title: string;
  body: string;
  complaint_id: number | null;
  complaint_number: string | null;
  is_read: boolean;
  created_at: string;
}
export interface CategoryItem {
  id: number;
  name: string;
  code: string;
  description?: string | null;
  department_id: number;
  department?: DepartmentRef;
  is_active: boolean;
}
export interface DepartmentItem {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
}
export interface ActivitySummary {
  by_status?: Record<string, number>;
  by_department?: { id: number; name: string; open: number; escalated?: number }[];
  escalations_total?: number;
  escalation_window_minutes?: number;
  demo_mode?: boolean;
  recent_events?: TimelineEvent[];
}
export interface AuditLogItem {
  id: number;
  actor_user_id: number | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  meta?: Record<string, unknown> | null;
  created_at: string;
}
export interface DepartmentSummary {
  by_status?: Record<string, number>;
  open?: number;
  escalated?: number;
  overdue?: number;
}
export interface EscalationSummary {
  open?: number;
  oldest_overdue_seconds?: number;
  by_department?: { id: number; name: string; open: number }[];
}
