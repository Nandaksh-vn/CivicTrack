import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AppRoutes } from "@/router/AppRoutes";

describe("AppRoutes", () => {
  it("renders the CivicTrack landing page", () => {
    render(
      <MemoryRouter>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", {
        name: /public issues, tracked to resolution/i,
      }),
    ).toBeInTheDocument();
  });

  it("renders a not-found page for unknown routes", () => {
    render(
      <MemoryRouter initialEntries={["/unknown"]}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { name: /that page does not exist/i }),
    ).toBeInTheDocument();
  });
});
