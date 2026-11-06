import { apiFetch } from "@/api/client";

function queryString(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}
import type {
  ActivitySummary,
  AuditLogItem,
  CategoryItem,
  ComplaintDetail,
  ComplaintSummary,
  DepartmentItem,
  DepartmentSummary,
  EscalationSummary,
  NotificationItem,
  Page,
  TimelineEvent,
  TokenResponse,
  User,
} from "@/api/types";

export const authApi = {
  register: (payload: { full_name: string; email: string; password: string; phone?: string }) =>
    apiFetch<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  login: (payload: { email: string; password: string }) =>
    apiFetch<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => apiFetch<void>("/auth/logout", { method: "POST" }).catch(() => undefined),
  me: () => apiFetch<User>("/auth/me"),
};

export const categoriesApi = {
  list: () => apiFetch<{ items: CategoryItem[] }>("/categories"),
};

export const complaintsApi = {
  list: (params: Record<string, string | number | boolean | undefined>) =>
    apiFetch<Page<ComplaintSummary>>(`/complaints${queryString(params)}`),
  detail: (id: string | number) => apiFetch<ComplaintDetail>(`/complaints/${id}`),
  timeline: (id: string | number) =>
    apiFetch<{ items: TimelineEvent[] }>(`/complaints/${id}/timeline`),
  create: (form: FormData) =>
    apiFetch<ComplaintDetail>("/complaints", { method: "POST", body: form }),
  uploadEvidence: (id: string | number, form: FormData) =>
    apiFetch<{ items: unknown[] }>(`/complaints/${id}/images`, { method: "POST", body: form }),
};

export const departmentApi = {
  queue: (params: Record<string, string | number | boolean | undefined>) =>
    apiFetch<Page<ComplaintSummary>>(`/department/complaints${queryString(params)}`),
  summary: () => apiFetch<DepartmentSummary>("/department/summary"),
  accept: (id: string | number) =>
    apiFetch<unknown>(`/complaints/${id}/accept`, { method: "POST", body: "{}" }),
  reject: (id: string | number, reason: string) =>
    apiFetch<unknown>(`/complaints/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  assign: (id: string | number, assignee_user_id: number) =>
    apiFetch<unknown>(`/complaints/${id}/assign`, {
      method: "POST",
      body: JSON.stringify({ assignee_user_id }),
    }),
  progress: (id: string | number, payload: { note: string; set_status?: string }) =>
    apiFetch<unknown>(`/complaints/${id}/progress`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resolve: (id: string | number, resolution_note: string) =>
    apiFetch<unknown>(`/complaints/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ resolution_note }),
    }),
};

export const superintendentApi = {
  escalations: (params: Record<string, string | number | boolean | undefined>) =>
    apiFetch<Page<ComplaintSummary>>(`/superintendent/escalations${queryString(params)}`),
  summary: () => apiFetch<EscalationSummary>("/superintendent/summary"),
  action: (
    id: string | number,
    payload: { action_type: string; note: string; directed_department_id?: number },
  ) =>
    apiFetch<unknown>(`/complaints/${id}/superintendent-actions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resolve: (id: string | number, resolution_note: string) =>
    apiFetch<unknown>(`/complaints/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ resolution_note }),
    }),
};

export const notificationsApi = {
  list: (params: Record<string, string | number | boolean | undefined>) =>
    apiFetch<Page<NotificationItem>>(`/notifications${queryString(params)}`),
  unreadCount: () => apiFetch<{ unread_count: number }>("/notifications/unread-count"),
  markRead: (id: number) =>
    apiFetch<NotificationItem>(`/notifications/${id}/read`, { method: "POST", body: "{}" }),
  markAllRead: () =>
    apiFetch<{ updated: number }>("/notifications/read-all", { method: "POST", body: "{}" }),
};

export const adminApi = {
  users: (params: Record<string, string | number | boolean | undefined>) =>
    apiFetch<Page<User>>(`/admin/users${queryString(params)}`),
  createUser: (payload: Record<string, unknown>) =>
    apiFetch<User>("/admin/users", { method: "POST", body: JSON.stringify(payload) }),
  updateUser: (id: number, payload: Record<string, unknown>) =>
    apiFetch<User>(`/admin/users/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  departments: () => apiFetch<{ items: DepartmentItem[] }>("/admin/departments"),
  createDepartment: (payload: Record<string, unknown>) =>
    apiFetch<DepartmentItem>("/admin/departments", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateDepartment: (id: number, payload: Record<string, unknown>) =>
    apiFetch<DepartmentItem>(`/admin/departments/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  categories: () => apiFetch<{ items: CategoryItem[] }>("/admin/categories"),
  createCategory: (payload: Record<string, unknown>) =>
    apiFetch<CategoryItem>("/admin/categories", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateCategory: (id: number, payload: Record<string, unknown>) =>
    apiFetch<CategoryItem>(`/admin/categories/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  activity: () => apiFetch<ActivitySummary>("/admin/activity"),
  auditLogs: (params: Record<string, string | number | boolean | undefined>) =>
    apiFetch<Page<AuditLogItem>>(`/admin/audit-logs${queryString(params)}`),
};
