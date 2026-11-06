import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ApiError } from "@/api/client";
import { adminApi } from "@/api/modules";
import { FormField, inputClass } from "@/components/forms/FormField";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/states/PageStates";
import { Button } from "@/components/ui/button";

export default function AdminDepartmentsPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const departments = useQuery({
    queryKey: ["admin", "departments"],
    queryFn: adminApi.departments,
  });

  const create = useMutation({
    mutationFn: () => adminApi.createDepartment({ name, code }),
    onSuccess: () => {
      setNotice("Department created.");
      setName("");
      setCode("");
      void queryClient.invalidateQueries({ queryKey: ["admin", "departments"] });
    },
    onError: (error: unknown) =>
      setNotice(error instanceof ApiError ? error.message : "Create failed."),
  });
  const update = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      adminApi.updateDepartment(id, payload),
    onSuccess: () => {
      setNotice("Department updated.");
      void queryClient.invalidateQueries({ queryKey: ["admin", "departments"] });
    },
    onError: (error: unknown) =>
      setNotice(
        error instanceof ApiError
          ? "This department cannot be deactivated while it still owns categories or open complaints."
          : "Update failed.",
      ),
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">Departments</h1>
      <form
        className="grid gap-3 sm:grid-cols-3"
        onSubmit={(event) => {
          event.preventDefault();
          create.mutate();
        }}
      >
        <FormField label="Name" htmlFor="dept-name">
          <input
            id="dept-name"
            className={inputClass}
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </FormField>
        <FormField label="Code" htmlFor="dept-code">
          <input
            id="dept-code"
            className={inputClass}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
          />
        </FormField>
        <div className="flex items-end">
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Creating…" : "Create department"}
          </Button>
        </div>
      </form>
      {notice ? (
        <p role="status" className="text-sm font-medium">
          {notice}
        </p>
      ) : null}
      {departments.isLoading ? (
        <LoadingSkeleton />
      ) : departments.error ? (
        <ErrorState
          message="We could not load departments."
          onRetry={() => void departments.refetch()}
        />
      ) : departments.data && departments.data.items.length === 0 ? (
        <EmptyState
          title="No departments"
          message="Create a department to route complaints to it."
        />
      ) : (
        <ul className="space-y-3">
          {(departments.data?.items ?? []).map((dept) => (
            <li
              key={dept.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-4"
            >
              <div>
                <p className="font-medium">{dept.name}</p>
                <p className="text-sm text-muted-foreground">
                  {dept.code} · {dept.is_active ? "Active" : "Inactive"}
                </p>
              </div>
              <Button
                size="sm"
                variant="outline"
                disabled={update.isPending}
                onClick={() =>
                  update.mutate({ id: dept.id, payload: { is_active: !dept.is_active } })
                }
              >
                {dept.is_active ? "Deactivate" : "Activate"}
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
