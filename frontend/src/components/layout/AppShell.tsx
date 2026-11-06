import { useQuery } from "@tanstack/react-query";
import { Bell, ShieldCheck } from "lucide-react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import { notificationsApi } from "@/api/modules";
import { useAuth } from "@/features/auth/AuthProvider";
import { DEMO_ESCALATION_SHORT, isDemoEscalationEnabled, type UserRole } from "@/lib/status";

const NAV: Record<UserRole, { to: string; label: string }[]> = {
  CITIZEN: [
    { to: "/complaints", label: "My Complaints" },
    { to: "/complaints/new", label: "Report a Problem" },
    { to: "/notifications", label: "Notifications" },
    { to: "/profile", label: "Profile" },
  ],
  DEPARTMENT_OFFICER: [
    { to: "/department", label: "Department Queue" },
    { to: "/department/summary", label: "Department Summary" },
    { to: "/notifications", label: "Notifications" },
    { to: "/profile", label: "Profile" },
  ],
  SUPERINTENDENT_OFFICER: [
    { to: "/superintendent", label: "Escalation Queue" },
    { to: "/superintendent/summary", label: "Escalation Summary" },
    { to: "/notifications", label: "Notifications" },
    { to: "/profile", label: "Profile" },
  ],
  PLATFORM_ADMIN: [
    { to: "/admin/users", label: "Users" },
    { to: "/admin/departments", label: "Departments" },
    { to: "/admin/categories", label: "Categories" },
    { to: "/admin/activity", label: "Activity" },
    { to: "/admin/audit", label: "Audit Log" },
    { to: "/notifications", label: "Notifications" },
    { to: "/profile", label: "Profile" },
  ],
};

function AuthedShell({ user }: { user: NonNullable<ReturnType<typeof useAuth>["user"]> }) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const unread = useQuery({
    queryKey: ["unread-count"],
    queryFn: notificationsApi.unreadCount,
    refetchInterval: 30_000,
  });
  const links = NAV[user.role];

  return (
    <>
      <HeaderChrome
        links={links}
        user={user}
        unreadCount={unread.data?.unread_count ?? 0}
        onLogout={() => void logout().then(() => navigate("/login"))}
      />
      <main className="flex-1">
        <Outlet />
      </main>
      <ShellFooter />
    </>
  );
}

export function AppShell() {
  const { user } = useAuth();
  if (user) {
    return (
      <div className="flex min-h-screen flex-col bg-background text-foreground">
        <AuthedShell user={user} />
      </div>
    );
  }
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <HeaderChrome links={[]} onLogout={() => {}} />
      <main className="flex-1">
        <Outlet />
      </main>
      <ShellFooter />
    </div>
  );
}

function ShellFooter() {
  return (
    <footer className="border-t border-border/80">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-1 px-6 py-5 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <span>CivicTrack - community issues, tracked to resolution.</span>
        <span>React + Vite + FastAPI + MySQL</span>
      </div>
    </footer>
  );
}

interface HeaderChromeProps {
  links: { to: string; label: string }[];
  user?: { full_name: string; role: string };
  unreadCount?: number;
  onLogout: () => void;
}

function HeaderChrome({ links, user, unreadCount = 0, onLogout }: HeaderChromeProps) {
  return (
    <header className="border-b border-border/80 bg-background/90 backdrop-blur">
      <div className="mx-auto flex min-h-16 w-full max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-3">
        <Link className="flex items-center gap-2 font-semibold tracking-tight" to="/">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ShieldCheck className="h-4 w-4" aria-hidden="true" />
          </span>
          CivicTrack
        </Link>
        <div className="flex items-center gap-3">
          {isDemoEscalationEnabled() ? (
            <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900">
              {DEMO_ESCALATION_SHORT}
            </span>
          ) : null}
          {user ? (
            <>
              <Link
                to="/notifications"
                aria-label="Notifications"
                className="relative rounded-md p-2 hover:bg-accent"
              >
                <Bell className="h-5 w-5" aria-hidden="true" />
                {unreadCount > 0 ? (
                  <span className="absolute -right-1 -top-1 rounded-full bg-destructive px-1.5 text-[11px] font-bold text-destructive-foreground">
                    {unreadCount}
                  </span>
                ) : null}
              </Link>
              <span className="text-sm text-muted-foreground">
                {user.full_name} · {user.role.replaceAll("_", " ")}
              </span>
              <button
                type="button"
                className="text-sm font-medium underline-offset-4 hover:underline"
                onClick={onLogout}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link className="text-sm font-medium hover:underline" to="/login">
                Log in
              </Link>
              <Link className="text-sm font-medium hover:underline" to="/register">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
      {links.length > 0 ? (
        <nav
          aria-label="Primary"
          className="mx-auto flex w-full max-w-6xl flex-wrap gap-1 px-6 pb-3"
        >
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 text-sm font-medium ${isActive ? "bg-secondary text-secondary-foreground" : "hover:bg-accent"}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      ) : null}
    </header>
  );
}
