import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { adminApi } from "@/api/modules";
import { ApiError } from "@/api/client";
import { FormField, inputClass } from "@/components/forms/FormField";
import { Pagination } from "@/components/layout/Pagination";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/states/PageStates";
import { Button } from "@/components/ui/button";

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "CITIZEN",
    department_id: "",
  });
  const [notice, setNotice] = useState<string | null>(null);
  const users = useQuery({
    queryKey: ["admin", "users", page],
    queryFn: () => adminApi.users({ page, page_size: 20 }),
  });
  const departments = useQuery({
    queryKey: ["admin", "departments"],
    queryFn: adminApi.departments,
  });

  const create = useMutation({
    mutationFn: () =>
      adminApi.createUser({
        full_name: form.full_name,
        email: form.email,
        password: form.password,
        role: form.role,
        department_id: form.department_id ? Number(form.department_id) : null,
      }),
    onSuccess: () => {
      setNotice("User created.");
      setForm({ full_name: "", email: "", password: "", role: "CITIZEN", department_id: "" });
      void queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
    onError: (error: unknown) =>
      setNotice(error instanceof ApiError ? error.message : "Create failed."),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      adminApi.updateUser(id, payload),
    onSuccess: () => {
      setNotice("User updated.");
      void queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
    onError: (error: unknown) =>
      setNotice(
        error instanceof ApiError && error.code === "LAST_ADMIN"
          ? "You cannot deactivate or demote the last active administrator."
          : error instanceof Error
            ? error.message
            : "Update failed.",
      ),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">Users</h1>
      <form
        className="grid gap-3 rounded-xl border border-border bg-card p-4 sm:grid-cols-2"
        onSubmit={(event) => {
          event.preventDefault();
          create.mutate();
        }}
      >
        <FormField label="Full name" htmlFor="new-name">
          <input
            id="new-name"
            className={inputClass}
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            required
          />
        </FormField>
        <FormField label="Email" htmlFor="new-email">
          <input
            id="new-email"
            type="email"
            className={inputClass}
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </FormField>
        <FormField label="Password" htmlFor="new-password">
          <input
            id="new-password"
            type="password"
            className={inputClass}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
        </FormField>
        <FormField label="Role" htmlFor="new-role">
          <select
            id="new-role"
            className={inputClass}
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
          >
            <option value="CITIZEN">Citizen</option>
            <option value="DEPARTMENT_OFFICER">Department Officer</option>
            <option value="SUPERINTENDENT_OFFICER">Superintendent Officer</option>
            <option value="PLATFORM_ADMIN">Platform Admin</option>
          </select>
        </FormField>
        <FormField label="Department (officers)" htmlFor="new-department">
          <select
            id="new-department"
            className={inputClass}
            value={form.department_id}
            onChange={(e) => setForm({ ...form, department_id: e.target.value })}
          >
            <option value="">None</option>
            {(departments.data?.items ?? []).map((dept) => (
              <option key={dept.id} value={dept.id}>
                {dept.name}
              </option>
            ))}
          </select>
        </FormField>
        <div className="flex items-end">
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Creating…" : "Create user"}
          </Button>
        </div>
      </form>
      {notice ? (
        <p role="status" className="text-sm font-medium">
          {notice}
        </p>
      ) : null}
      {users.isLoading ? (
        <LoadingSkeleton />
      ) : users.error ? (
        <ErrorState message="We could not load users." onRetry={() => void users.refetch()} />
      ) : users.data && users.data.items.length === 0 ? (
        <EmptyState title="No users" message="Create the first officer or admin account above." />
      ) : (
        <>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted-foreground">
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Email</th>
                <th className="py-2 pr-4">Role</th>
                <th className="py-2 pr-4">Department</th>
                <th className="py-2 pr-4">Active</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(users.data?.items ?? []).map((user) => (
                <tr key={user.id} className="border-t border-border">
                  <td className="py-2 pr-4">{user.full_name}</td>
                  <td className="py-2 pr-4">{user.email}</td>
                  <td className="py-2 pr-4">
                    <select
                      aria-label={`Role for ${user.full_name}`}
                      className="h-9 rounded-md border border-input bg-background px-2"
                      value={user.role}
                      disabled={update.isPending}
                      onChange={(e) =>
                        update.mutate({ id: user.id, payload: { role: e.target.value } })
                      }
                    >
                      <option value="CITIZEN">Citizen</option>
                      <option value="DEPARTMENT_OFFICER">Department Officer</option>
                      <option value="SUPERINTENDENT_OFFICER">Superintendent</option>
                      <option value="PLATFORM_ADMIN">Platform Admin</option>
                    </select>
                  </td>
                  <td className="py-2 pr-4">{user.department?.name ?? "—"}</td>
                  <td className="py-2 pr-4">{user.is_active ? "Yes" : "No"}</td>
                  <td className="py-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={update.isPending}
                      onClick={() =>
                        update.mutate({ id: user.id, payload: { is_active: !user.is_active } })
                      }
                    >
                      {user.is_active ? "Deactivate" : "Activate"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination
            page={users.data?.page ?? page}
            totalPages={users.data?.total_pages ?? 1}
            onPage={setPage}
          />
        </>
      )}
    </div>
  );
}
