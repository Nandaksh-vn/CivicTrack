import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { FormField } from "@/components/forms/FormField";

describe("FormField", () => {
  it("renders label and children", () => {
    render(
      <FormField label="Email" htmlFor="email">
        <input id="email" />
      </FormField>,
    );
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Email" })).toBeInTheDocument();
  });

  it("renders hint text when provided", () => {
    render(
      <FormField label="Phone" htmlFor="phone" hint="Optional phone number.">
        <input id="phone" />
      </FormField>,
    );
    expect(screen.getByText("Optional phone number.")).toBeInTheDocument();
  });

  it("renders error with role=alert when provided", () => {
    render(
      <FormField label="Password" htmlFor="password" error="Too short.">
        <input id="password" />
      </FormField>,
    );
    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveTextContent("Too short.");
  });

  it("does not render error when not provided", () => {
    render(
      <FormField label="Name" htmlFor="name">
        <input id="name" />
      </FormField>,
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
