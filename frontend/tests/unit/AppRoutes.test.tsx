import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { AppRoutes } from "@/router/AppRoutes";
import { AuthContext } from "@/providers/AuthContext";
import type { PublicUser } from "@/types";

function renderRoutes(
  initialEntries: string[] = ["/"],
  user: PublicUser | null = null,
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <AuthContext.Provider
          value={{
            user,
            status: "authenticated",
            isAuthenticated: user != null,
            login: async () => user as PublicUser,
            register: async () => user as PublicUser,
            logout: async () => {},
          }}
        >
          <AppRoutes />
        </AuthContext.Provider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AppRoutes", () => {
  it("redirects to login when unauthenticated", () => {
    renderRoutes(["/"], null);
    expect(screen.getByRole("heading", { name: /log in to civictrack/i })).toBeInTheDocument();
  });

  it("renders a not-found page for unknown routes", () => {
    renderRoutes(["/unknown"], { role: "CITIZEN" } as PublicUser);
    expect(
      screen.getByRole("heading", { name: /that page does not exist/i }),
    ).toBeInTheDocument();
  });
});
