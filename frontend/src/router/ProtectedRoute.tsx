import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { ForbiddenPage, LoadingSkeleton } from "@/components/states/PageStates";
import { useAuth } from "@/features/auth/AuthProvider";
import type { UserRole } from "@/lib/status";

export function ProtectedRoute({ children, roles }: { children: ReactNode; roles?: UserRole[] }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <LoadingSkeleton />;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <ForbiddenPage />;
  return <>{children}</>;
}

export function PublicOnly({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <LoadingSkeleton />;
  if (user) {
    const home =
      user.role === "CITIZEN"
        ? "/complaints"
        : user.role === "DEPARTMENT_OFFICER"
          ? "/department"
          : user.role === "SUPERINTENDENT_OFFICER"
            ? "/superintendent"
            : "/admin/users";
    return <Navigate to={home} replace />;
  }
  return <>{children}</>;
}
