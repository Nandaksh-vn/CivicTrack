import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/api/client";
import { AppShell } from "@/components/layout/AppShell";
import { AuthContext } from "@/providers/AuthContext";
import { AppRoutes } from "@/router/AppRoutes";
import { fieldErrorsFrom } from "@/lib/fieldErrors";
import { DEMO_ESCALATION_LABEL, statusMeta } from "@/lib/status";
import type { PublicUser } from "@/types";

function userWithRole(role: PublicUser["role"]): PublicUser {
  return {
    id: 1,
    full_name: "Test User",
    email: "test@example.com",
    phone: null,
    role,
    department: null,
    is_active: true,
  };
}

function renderWithShell(user: PublicUser) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AuthContext.Provider
          value={{
            user,
            status: "authenticated",
            isAuthenticated: true,
            login: async () => user,
            register: async () => user,
            logout: async () => {},
          }}
        >
          <AppShell />
        </AuthContext.Provider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("role navigation (TEST-034, AC-13)", () => {
  it("citizen sees only citizen navigation", () => {
    renderWithShell(userWithRole("CITIZEN"));
    expect(screen.getByRole("link", { name: /my complaints/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /report a problem/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /department queue/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /escalation queue/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /users/i })).not.toBeInTheDocument();
  });

  it("department officer sees only department navigation", () => {
    renderWithShell(userWithRole("DEPARTMENT_OFFICER"));
    expect(screen.getByRole("link", { name: /department queue/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /my complaints/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /escalation queue/i })).not.toBeInTheDocument();
  });

  it("superintendent sees only escalation navigation", () => {
    renderWithShell(userWithRole("SUPERINTENDENT_OFFICER"));
    expect(screen.getByRole("link", { name: /escalation queue/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /department queue/i })).not.toBeInTheDocument();
  });

  it("admin sees only admin navigation", () => {
    renderWithShell(userWithRole("PLATFORM_ADMIN"));
    expect(screen.getByRole("link", { name: /^users$/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /audit log/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /my complaints/i })).not.toBeInTheDocument();
  });

  it("citizen direct URL to department workspace shows forbidden", () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const user = userWithRole("CITIZEN");
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/department"]}>
          <AuthContext.Provider
            value={{
              user,
              status: "authenticated",
              isAuthenticated: true,
              login: async () => user,
              register: async () => user,
              logout: async () => {},
            }}
          >
            <AppRoutes />
          </AuthContext.Provider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(screen.getByRole("heading", { name: /you do not have access/i })).toBeInTheDocument();
  });
});

describe("copy rules (FE-037, BR-12)", () => {
  it("never claims verification in status labels", () => {
    const labels = Object.values(statusMeta).map((meta) => meta.label.toLowerCase());
    expect(labels.join(" ")).not.toMatch(/verif/);
    expect(labels).toContain("escalated to superintendent");
  });

  it("demo escalation window is labeled visibly", () => {
    expect(DEMO_ESCALATION_LABEL).toMatch(/demo escalation window/i);
    expect(DEMO_ESCALATION_LABEL).toMatch(/10 minutes/);
  });
});

describe("server 422 field mapping (TEST-035)", () => {
  it("maps details.fields onto form fields", () => {
    const error = new ApiError(422, "VALIDATION_ERROR", "The request is invalid.", {
      fields: [
        { field: "title", message: "Title must be at least 5 characters." },
        { field: "category_id", message: "Choose a category." },
      ],
    });
    expect(fieldErrorsFrom(error)).toEqual({
      title: "Title must be at least 5 characters.",
      category_id: "Choose a category.",
    });
  });

  it("returns empty map for non-ApiError failures", () => {
    expect(fieldErrorsFrom(new Error("boom"))).toEqual({});
  });
});

describe("timed first-time submission surface (TEST-033)", () => {
  it("new-complaint form has at most five required inputs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify({ items: [] }), {
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const user = userWithRole("CITIZEN");
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/complaints/new"]}>
          <AuthContext.Provider
            value={{
              user,
              status: "authenticated",
              isAuthenticated: true,
              login: async () => user,
              register: async () => user,
              logout: async () => {},
            }}
          >
            <AppRoutes />
          </AuthContext.Provider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    // Required inputs: category, title, description (+ optional location/photos).
    expect(screen.getByLabelText(/category/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^title$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/location \(optional\)/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /submit complaint/i })).toBeInTheDocument();
  });
});
