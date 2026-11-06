import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "@/api/client";
import { FormField, inputClass } from "@/components/forms/FormField";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/AuthProvider";
import { loginSchema, type LoginValues } from "@/lib/validators";
import { roleHome } from "@/lib/status";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    mode: "onBlur",
  });

  async function onSubmit(values: LoginValues) {
    setServerError(null);
    try {
      const user = await login(values.email, values.password);
      navigate(roleHome(user.role), { replace: true });
    } catch (error) {
      if (
        error instanceof ApiError &&
        (error.status === 401 || error.code === "INVALID_CREDENTIALS")
      ) {
        // Generic message by design: never reveal whether the email exists.
        setServerError("Email or password is incorrect.");
      } else if (error instanceof ApiError && error.status === 429) {
        setServerError("Too many attempts. Please wait and try again.");
      } else {
        setServerError(error instanceof Error ? error.message : "Login failed.");
      }
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 py-16">
      <h1 className="text-2xl font-semibold tracking-tight">Log in to CivicTrack</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Use the email and password for your account.
      </p>
      <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
        <FormField label="Email" htmlFor="email" error={form.formState.errors.email?.message}>
          <input
            id="email"
            type="email"
            autoComplete="email"
            className={inputClass}
            {...form.register("email")}
          />
        </FormField>
        <FormField
          label="Password"
          htmlFor="password"
          error={form.formState.errors.password?.message}
        >
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            className={inputClass}
            {...form.register("password")}
          />
        </FormField>
        {serverError ? (
          <p role="alert" className="text-sm font-medium text-destructive">
            {serverError}
          </p>
        ) : null}
        <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Logging in…" : "Log in"}
        </Button>
      </form>
      <p className="mt-4 text-sm text-muted-foreground">
        New here?{" "}
        <Link className="font-medium text-primary hover:underline" to="/register">
          Create a citizen account
        </Link>
      </p>
    </div>
  );
}
