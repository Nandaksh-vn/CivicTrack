import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { AuthContext } from "@/providers/AuthContext";
import type { PublicUser } from "@/types";
import { ApiError } from "@/api/client";
import LoginPage from "@/pages/auth/LoginPage";

function renderLogin({
  user,
  isLoading,
  login,
}: {
  user: PublicUser | null;
  isLoading: boolean;
  login?: () => Promise<PublicUser>;
}) {
  return render(
    <MemoryRouter>
      <AuthContext.Provider
        value={{
          user,
          status: isLoading ? "loading" : "authenticated",
          isAuthenticated: !isLoading && user != null,
          login: login ?? (async () => user as PublicUser),
          register: async () => user as PublicUser,
          logout: async () => {},
        }}
      >
        <LoginPage />
      </AuthContext.Provider>
    </MemoryRouter>,
  );
}

describe("LoginPage", () => {
  it("renders heading and form fields", () => {
    renderLogin({ user: null, isLoading: false, login: async () => null as unknown as PublicUser });
    expect(screen.getByRole("heading", { name: /log in to civictrack/i })).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log in/i })).toBeInTheDocument();
  });

  it("shows link to register page", () => {
    renderLogin({ user: null, isLoading: false, login: async () => null as unknown as PublicUser });
    expect(screen.getByText(/new here\?/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create a citizen account/i })).toBeInTheDocument();
  });

  it("disables submit button while logging in", async () => {
    const holder: { resolveLogin: (() => void) | null } = { resolveLogin: null };
    const login = async () => {
      return new Promise<PublicUser>(() => {
        holder.resolveLogin = () => {};
      });
    };
    renderLogin({ user: null, isLoading: false, login });
    const submit = screen.getByRole("button", { name: /log in/i });
    expect(submit).not.toBeDisabled();
    holder.resolveLogin?.();
  });

  it("shows server error on failed login", async () => {
    const login = async () => {
      throw new ApiError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.");
    };
    renderLogin({ user: null, isLoading: false, login });

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@b.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: /log in/i }));

    expect(await screen.findByText(/email or password is incorrect/i)).toBeInTheDocument();
  });
});
