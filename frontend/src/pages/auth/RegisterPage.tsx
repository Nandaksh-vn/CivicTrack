import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "@/api/client";
import { FormField, inputClass } from "@/components/forms/FormField";
import { fieldErrorsFrom } from "@/lib/fieldErrors";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/AuthProvider";
import { registerSchema, type RegisterValues } from "@/lib/validators";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    mode: "onBlur",
  });

  async function onSubmit(values: RegisterValues) {
    setServerError(null);
    try {
      await register({
        full_name: values.full_name,
        email: values.email,
        password: values.password,
        phone: values.phone || undefined,
      });
      navigate("/complaints/new", { replace: true });
    } catch (error) {
      if (error instanceof ApiError) {
        const fields = fieldErrorsFrom(error);
        for (const [field, message] of Object.entries(fields)) {
          form.setError(field as never, { message });
        }
        if (error.code === "EMAIL_ALREADY_REGISTERED") {
          form.setError("email", { message: "An account with this email already exists." });
        } else if (Object.keys(fields).length === 0) {
          setServerError(error.message);
        }
      } else {
        setServerError(error instanceof Error ? error.message : "Registration failed.");
      }
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 py-16">
      <h1 className="text-2xl font-semibold tracking-tight">Create your citizen account</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Reports go to the department responsible for the category you choose.
      </p>
      <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="mt-6 space-y-4">
        <FormField
          label="Full name"
          htmlFor="full_name"
          error={form.formState.errors.full_name?.message}
        >
          <input
            id="full_name"
            autoComplete="name"
            className={inputClass}
            {...form.register("full_name")}
          />
        </FormField>
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
          hint="At least 8 characters."
          error={form.formState.errors.password?.message}
        >
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            className={inputClass}
            {...form.register("password")}
          />
        </FormField>
        <FormField
          label="Phone (optional)"
          htmlFor="phone"
          error={form.formState.errors.phone?.message}
        >
          <input
            id="phone"
            type="tel"
            autoComplete="tel"
            className={inputClass}
            {...form.register("phone")}
          />
        </FormField>
        {serverError ? (
          <p role="alert" className="text-sm font-medium text-destructive">
            {serverError}
          </p>
        ) : null}
        <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Creating account…" : "Create account"}
        </Button>
      </form>
      <p className="mt-4 text-sm text-muted-foreground">
        Already registered?{" "}
        <Link className="font-medium text-primary hover:underline" to="/login">
          Log in
        </Link>
      </p>
    </div>
  );
}
