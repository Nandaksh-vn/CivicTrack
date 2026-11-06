import {
  Activity,
  Bell,
  ClipboardList,
  FolderKanban,
  LayoutDashboard,
  ListChecks,
  ShieldCheck,
  TriangleAlert,
  UserRound,
  Building2,
  Shapes,
  ScrollText,
  Users,
  type LucideIcon,
} from "lucide-react";

import type { Role } from "@/types";

export interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  /** Which authenticated roles see this item. */
  roles: Role[];
}

const AUTHENTICATED: Role[] = [
  "CITIZEN",
  "DEPARTMENT_OFFICER",
  "SUPERINTENDENT_OFFICER",
  "PLATFORM_ADMIN",
];

export const NAV_ITEMS: NavItem[] = [
  { label: "Complaints", to: "/complaints", icon: ClipboardList, roles: ["CITIZEN"] },
  { label: "New complaint", to: "/complaints/new", icon: ListChecks, roles: ["CITIZEN"] },
  { label: "Notifications", to: "/notifications", icon: Bell, roles: AUTHENTICATED },
  { label: "Department queue", to: "/department", icon: FolderKanban, roles: ["DEPARTMENT_OFFICER"] },
  { label: "Escalations", to: "/superintendent", icon: TriangleAlert, roles: ["SUPERINTENDENT_OFFICER"] },
  { label: "Users", to: "/admin/users", icon: Users, roles: ["PLATFORM_ADMIN"] },
  { label: "Departments", to: "/admin/departments", icon: Building2, roles: ["PLATFORM_ADMIN"] },
  { label: "Categories", to: "/admin/categories", icon: Shapes, roles: ["PLATFORM_ADMIN"] },
  { label: "Activity", to: "/admin/activity", icon: Activity, roles: ["PLATFORM_ADMIN"] },
  { label: "Audit logs", to: "/admin/audit-logs", icon: ScrollText, roles: ["PLATFORM_ADMIN"] },
  { label: "Profile", to: "/profile", icon: UserRound, roles: AUTHENTICATED },
];

export function navForRole(role: Role | null | undefined): NavItem[] {
  if (!role) {
    return [];
  }
  return NAV_ITEMS.filter((item) => item.roles.includes(role));
}

/** Where a role lands after login / from "/" when signed in. */
export function homePathForRole(role: Role | null | undefined): string {
  switch (role) {
    case "CITIZEN":
      return "/complaints";
    case "DEPARTMENT_OFFICER":
      return "/department";
    case "SUPERINTENDENT_OFFICER":
      return "/superintendent";
    case "PLATFORM_ADMIN":
      return "/admin/users";
    default:
      return "/";
  }
}

export const brandIdentity = {
  name: "CivicTrack",
  icon: ShieldCheck,
  homeIcon: LayoutDashboard,
} as const;
