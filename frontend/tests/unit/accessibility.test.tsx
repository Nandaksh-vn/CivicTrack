/** TEST-032: axe accessibility audit of the shell, states, and forms. */

import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import axe from "axe-core";

import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { AppShell } from "@/components/layout/AppShell";
import { createQueryClient } from "@/lib/query-client";
import { AuthProvider } from "@/providers/AuthProvider";

async function audit(container: HTMLElement) {
  const results = await axe.run(container, {
    // jsdom cannot measure real contrast; axe reports those checks as
    // incomplete rather than violations, and violations carry real signal.
    rules: {
      "color-contrast": { enabled: false },
    },
  });
  return results.violations;
}

describe("axe audits", () => {
  it("app shell (public chrome) has no violations", async () => {
    const { container, unmount } = render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter>
          <AuthProvider>
            <AppShell />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    const violations = await audit(container);
    unmount();
    expect(violations.map((violation) => violation.id)).toEqual([]);
  });

  it("error and empty states have no violations", async () => {
    const { container, unmount } = render(
      <MemoryRouter>
        <ErrorState title="Failed" message="Please retry." />
        <EmptyState title="Nothing yet" description="Report an issue." />
      </MemoryRouter>,
    );
    const violations = await audit(container);
    unmount();
    expect(violations.map((violation) => violation.id)).toEqual([]);
  });
});
