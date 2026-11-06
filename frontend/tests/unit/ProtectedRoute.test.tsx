import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { AuthContext } from "@/providers/AuthContext";
import { ProtectedRoute } from "@/router/ProtectedRoute";

function renderProtectedRoute(
  ui: React.ReactNode,
  { user, isLoading }: { user: object | null; isLoading: boolean },
) {
  return render(
    <MemoryRouter>
      <AuthContext.Provider
        value={{
          user: user as never,
          status: isLoading ? "loading" : "authenticated",
          isAuthenticated: !isLoading && user != null,
          login: async () => user as never,
          register: async () => user as never,
          logout: async () => {},
        }}
      >
        <ProtectedRoute roles={["CITIZEN"]}>{ui}</ProtectedRoute>
      </AuthContext.Provider>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  it("renders loading skeleton while auth is loading", () => {
    renderProtectedRoute(<div data-testid="inner">inner</div>, {
      user: null,
      isLoading: true,
    });
    expect(screen.getByLabelText(/loading/i)).toBeInTheDocument();
  });

  it("redirects to login when unauthenticated", () => {
    renderProtectedRoute(<div data-testid="inner">inner</div>, {
      user: null,
      isLoading: false,
    });
    expect(screen.queryByTestId("inner")).not.toBeInTheDocument();
  });

  it("renders children when user has allowed role", () => {
    renderProtectedRoute(<div data-testid="inner">inner</div>, {
      user: { role: "CITIZEN" },
      isLoading: false,
    });
    expect(screen.getByTestId("inner")).toBeInTheDocument();
  });

  it("renders forbidden when user role is not allowed", () => {
    renderProtectedRoute(<div data-testid="inner">inner</div>, {
      user: { role: "DEPARTMENT_OFFICER" },
      isLoading: false,
    });
    expect(screen.queryByTestId("inner")).not.toBeInTheDocument();
    expect(screen.getByText(/you do not have access to this page/i)).toBeInTheDocument();
  });
});
