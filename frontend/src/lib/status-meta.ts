import type { ComplaintPriority, ComplaintStatus, Role } from "@/types";

export type StatusMeta = {
  label: string;
  className: string;
};

const FALLBACK: StatusMeta = {
  label: "Unknown",
  className: "border-slate-200 bg-slate-100 text-slate-800",
};

/**
 * Single source of truth for complaint status labels and badge styling.
 * Text colors keep a contrast ratio of at least 4.5:1 on their backgrounds.
 */
export const complaintStatusMeta: Record<ComplaintStatus, StatusMeta> = {
  SUBMITTED: {
    label: "Submitted",
    className: "border-sky-200 bg-sky-100 text-sky-900",
  },
  PENDING_DEPARTMENT_REVIEW: {
    label: "Pending review",
    className: "border-amber-200 bg-amber-100 text-amber-900",
  },
  ACCEPTED: {
    label: "Accepted",
    className: "border-blue-200 bg-blue-100 text-blue-900",
  },
  IN_PROGRESS: {
    label: "In progress",
    className: "border-indigo-200 bg-indigo-100 text-indigo-900",
  },
  REJECTED: {
    label: "Rejected",
    className: "border-red-200 bg-red-100 text-red-900",
  },
  ESCALATED: {
    label: "Escalated",
    className: "border-orange-300 bg-orange-100 text-orange-900",
  },
  RESOLVED: {
    label: "Resolved",
    className: "border-emerald-200 bg-emerald-100 text-emerald-900",
  },
  REOPENED: {
    label: "Reopened",
    className: "border-purple-200 bg-purple-100 text-purple-900",
  },
};

export const priorityMeta: Record<ComplaintPriority, StatusMeta> = {
  LOW: { label: "Low", className: "border-slate-200 bg-slate-100 text-slate-800" },
  MEDIUM: { label: "Medium", className: "border-amber-200 bg-amber-100 text-amber-900" },
  HIGH: { label: "High", className: "border-red-200 bg-red-100 text-red-900" },
};

export const roleLabels: Record<Role, string> = {
  CITIZEN: "Citizen",
  DEPARTMENT_OFFICER: "Department Officer",
  SUPERINTENDENT_OFFICER: "Superintendent Officer",
  PLATFORM_ADMIN: "Platform Admin",
};

export function getComplaintStatusMeta(status?: string | null): StatusMeta {
  if (status && status in complaintStatusMeta) {
    return complaintStatusMeta[status as ComplaintStatus];
  }
  return status ? { ...FALLBACK, label: status } : FALLBACK;
}

export function getPriorityMeta(priority?: string | null): StatusMeta {
  if (priority && priority in priorityMeta) {
    return priorityMeta[priority as ComplaintPriority];
  }
  return priority ? { ...FALLBACK, label: priority } : FALLBACK;
}
