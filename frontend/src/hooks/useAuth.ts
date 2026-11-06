import { useContext } from "react";

import { AuthContext, type AuthContextValue } from "@/providers/AuthContext";

/** Access the auth session; throws outside `AuthProvider`. */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
