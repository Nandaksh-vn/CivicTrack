/* eslint-disable react-refresh/only-export-components -- co-located variant/context exports are intentional. */
/**
 * Phase 15 adapter over the shared AuthProvider (Phase 14 foundation).
 * Re-exports the canonical provider and a `useAuth` that also exposes
 * `isLoading` for route guards.
 */
import { useContext } from "react";

import { AuthContext } from "@/providers/AuthContext";
import type { PublicUser } from "@/types";

export { AuthProvider } from "@/providers/AuthProvider";

export interface Phase15Auth {
  user: PublicUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<PublicUser>;
  register: (payload: {
    full_name: string;
    email: string;
    password: string;
    phone?: string;
  }) => Promise<PublicUser>;
  logout: () => Promise<void>;
}

// The adapter deliberately re-exports both the provider and the hook so
// legacy call sites (AppRoutes, AppShell, pages) can import either.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): Phase15Auth {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return {
    user: ctx.user,
    isLoading: ctx.status === "loading",
    isAuthenticated: ctx.isAuthenticated,
    login: ctx.login,
    register: ctx.register,
    logout: ctx.logout,
  };
}
