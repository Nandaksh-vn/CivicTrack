/**
 * Query-key registry. Every TanStack Query call in the app uses these tuples
 * so caches invalidate predictably after mutations (TRD §17).
 */

export interface ComplaintListFilters {
  status?: string;
  category_id?: number;
  page?: number;
  page_size?: number;
}

export interface AdminUserFilters {
  role?: string;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export const queryKeys = {
  auth: {
    me: ["auth", "me"] as const,
  },
  categories: {
    all: ["categories"] as const,
  },
  complaints: {
    all: ["complaints"] as const,
    list: (filters: ComplaintListFilters = {}) =>
      ["complaints", "list", filters] as const,
    detail: (id: number | string) => ["complaints", "detail", String(id)] as const,
    timeline: (id: number | string) =>
      ["complaints", "detail", String(id), "timeline"] as const,
  },
  notifications: {
    all: ["notifications"] as const,
    list: (page = 1) => ["notifications", "list", { page }] as const,
    unreadCount: ["notifications", "unread-count"] as const,
  },
  department: {
    queue: (page = 1) => ["department", "complaints", { page }] as const,
  },
  superintendent: {
    escalations: (page = 1) =>
      ["superintendent", "escalations", { page }] as const,
  },
  admin: {
    users: (filters: AdminUserFilters = {}) => ["admin", "users", filters] as const,
    departments: ["admin", "departments"] as const,
    categories: ["admin", "categories"] as const,
    activity: (page = 1) => ["admin", "activity", { page }] as const,
    auditLogs: (page = 1) => ["admin", "audit-logs", { page }] as const,
  },
} as const;
