export type ComplaintStatus =
  | "SUBMITTED"
  | "PENDING_DEPARTMENT_REVIEW"
  | "ACCEPTED"
  | "IN_PROGRESS"
  | "REJECTED"
  | "ESCALATED"
  | "RESOLVED"
  | "REOPENED";

export type UserRole =
  "CITIZEN" | "DEPARTMENT_OFFICER" | "SUPERINTENDENT_OFFICER" | "PLATFORM_ADMIN";

export interface StatusMeta {
  label: string;
  badgeClass: string;
}

export const statusMeta: Record<ComplaintStatus, StatusMeta> = {
  SUBMITTED: { label: "Submitted", badgeClass: "bg-slate-100 text-slate-800" },
  PENDING_DEPARTMENT_REVIEW: {
    label: "Waiting for department review",
    badgeClass: "bg-amber-100 text-amber-900",
  },
  ACCEPTED: { label: "Accepted by department", badgeClass: "bg-blue-100 text-blue-900" },
  IN_PROGRESS: { label: "Work in progress", badgeClass: "bg-indigo-100 text-indigo-900" },
  REJECTED: { label: "Rejected", badgeClass: "bg-red-100 text-red-900" },
  ESCALATED: {
    label: "Escalated to Superintendent",
    badgeClass: "bg-orange-100 text-orange-900",
  },
  RESOLVED: { label: "Resolved", badgeClass: "bg-green-100 text-green-900" },
  REOPENED: { label: "Reopened", badgeClass: "bg-purple-100 text-purple-900" },
};

export function statusLabel(status: string): string {
  return statusMeta[status as ComplaintStatus]?.label ?? status.replaceAll("_", " ");
}

export const DEMO_ESCALATION_LABEL =
  "Demo escalation window: complaints escalate after 10 minutes (demo mode). In production the window is 7 days.";
export const DEMO_ESCALATION_SHORT = "Demo mode: 10-minute escalation window";

export function isDemoEscalationEnabled(): boolean {
  return import.meta.env.VITE_ALLOW_DEMO_ESCALATION === "true";
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function formatOverdue(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return "Not overdue";
  const total = Math.max(0, Math.floor(seconds));
  const days = Math.floor(total / 86400);
  const hours = Math.floor((total % 86400) / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h overdue`;
  if (hours > 0) return `${hours}h ${minutes}m overdue`;
  return `${minutes}m overdue`;
}

export function roleHome(role: UserRole): string {
  switch (role) {
    case "CITIZEN":
      return "/complaints";
    case "DEPARTMENT_OFFICER":
      return "/department";
    case "SUPERINTENDENT_OFFICER":
      return "/superintendent";
    case "PLATFORM_ADMIN":
      return "/admin/users";
  }
}
