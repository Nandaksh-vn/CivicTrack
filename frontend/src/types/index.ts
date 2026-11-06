/**
 * Shared frontend types mirroring the TRD contract (TRD §8, §5.2).
 * Role values match the backend enum exactly.
 */

export type Role =
  | "CITIZEN"
  | "DEPARTMENT_OFFICER"
  | "SUPERINTENDENT_OFFICER"
  | "PLATFORM_ADMIN";

export type ComplaintStatus =
  | "SUBMITTED"
  | "PENDING_DEPARTMENT_REVIEW"
  | "ACCEPTED"
  | "IN_PROGRESS"
  | "REJECTED"
  | "ESCALATED"
  | "RESOLVED"
  | "REOPENED";

export type ComplaintPriority = "LOW" | "MEDIUM" | "HIGH";

export type Department = {
  id: number;
  name: string;
  code: string;
  is_active?: boolean;
};

export type PublicUser = {
  id: number;
  full_name: string;
  email: string;
  phone: string | null;
  role: Role;
  department: Department | null;
  is_active: boolean;
};

export type TokenResponse = {
  token: string;
  token_type: string;
  expires_in: number;
  user: PublicUser;
};

/** Error envelope shared by every backend endpoint (TRD §5.4, §17). */
export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
  request_id?: string;
};

export type Page<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};
