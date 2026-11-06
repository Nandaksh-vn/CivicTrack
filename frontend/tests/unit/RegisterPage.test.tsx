import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { AuthContext } from "@/providers/AuthContext";
import type { PublicUser } from "@/types";
import { ApiError } from "@/api/client";
import RegisterPage from "@/pages/auth/RegisterPage";

function renderRegister({
  user,
  isLoading,
  register,
}: {
  user: PublicUser | null;
  isLoading: boolean;
  register?: () => Promise<PublicUser>;
}) {
  return render(
    <MemoryRouter>
      <AuthContext.Provider
        value={{
          user,
          status: isLoading ? "loading" : "authenticated",
          isAuthenticated: !isLoading && user != null,
          login: async () => user as PublicUser,
          register: register ?? (async () => user as PublicUser),
          logout: async () => {},
        }}
      >
        <RegisterPage />
      </AuthContext.Provider>
    </MemoryRouter>,
  );
}

describe("RegisterPage", () => {
  it("renders heading and form fields", () => {
    renderRegister({ user: null, isLoading: false, register: async () => null as unknown as PublicUser });
    expect(
      screen.getByRole("heading", { name: /create your citizen account/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Full name")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Phone (optional)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
  });

  it("shows link to login page", () => {
    renderRegister({ user: null, isLoading: false, register: async () => null as unknown as PublicUser });
    expect(screen.getByText(/already registered\?/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /log in/i })).toBeInTheDocument();
  });

  it("shows field error for duplicate email", async () => {
    const register = async () => {
      const err = new ApiError(
        409,
        "EMAIL_ALREADY_REGISTERED",
        "Email already registered.",
        { email: "An account with this email already exists." },
      );
      (err as unknown as { fieldErrors: () => Record<string, string> }).fieldErrors = () => ({
        email: "An account with this email already exists.",
      });
      throw err;
    };
    renderRegister({ user: null, isLoading: false, register });

    fireEvent.change(screen.getByLabelText("Full name"), { target: { value: "Test User" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@b.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(
      await screen.findByText(/an account with this email already exists/i),
    ).toBeInTheDocument();
  });

  it("shows generic server error when no field errors", async () => {
    const register = async () => {
      throw new Error("Registration failed.");
    };
    renderRegister({ user: null, isLoading: false, register });

    fireEvent.change(screen.getByLabelText("Full name"), { target: { value: "Test User" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@b.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByText(/registration failed/i)).toBeInTheDocument();
  });
});
