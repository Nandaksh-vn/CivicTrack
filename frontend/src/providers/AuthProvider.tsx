/**
 * AuthProvider: session is a bearer token kept in `sessionStorage`
 * (`civictrack.token`) plus the profile returned by `/auth/me`.
 *
 * The backend is the access-control authority; this provider only caches the
 * profile and exposes login/logout so the UI can hide what a role cannot use.
 * When the API client sees a 401 it clears the token, and this provider
 * subscribes to that store so every protected route reacts consistently.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { getMe, login as apiLogin, logout as apiLogout, register as apiRegister, setToken } from "@/api/client";
import { clearToken, getToken, subscribeToToken } from "@/lib/auth-token";
import { AuthContext, type AuthContextValue, type AuthStatus } from "@/providers/AuthContext";
import type { PublicUser } from "@/types";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<PublicUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>(() =>
    getToken() ? "loading" : "unauthenticated",
  );

  const bootstrap = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setStatus("unauthenticated");
      return;
    }
    setStatus("loading");
    try {
      const me = await getMe();
      setUser(me);
      setStatus("authenticated");
    } catch {
      clearToken();
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(
    () =>
      subscribeToToken((token) => {
        if (!token) {
          setUser(null);
          setStatus("unauthenticated");
        }
      }),
    [],
  );

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiLogin({ email, password });
    setToken(response.token);
    setUser(response.user);
    setStatus("authenticated");
    return response.user;
  }, []);

  const register = useCallback(
    async (input: {
      full_name: string;
      email: string;
      password: string;
      phone?: string;
    }) => {
      const response = await apiRegister(input);
      setToken(response.token);
      setUser(response.user);
      setStatus("authenticated");
      return response.user;
    },
    [],
  );

  const logout = useCallback(async () => {
    await apiLogout();
    clearToken();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      isAuthenticated: status === "authenticated",
      login,
      register,
      logout,
    }),
    [user, status, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
