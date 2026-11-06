import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ApiError } from "@/api/client";
import { adminApi } from "@/api/modules";
import { FormField, inputClass } from "@/components/forms/FormField";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/states/PageStates";
import { Button } from "@/components/ui/button";

export default function AdminCategoriesPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ name: "", code: "", department_id: "" });
  const [notice, setNotice] = useState<string | null>(null);
  const categories = useQuery({ queryKey: ["admin", "categories"], queryFn: adminApi.categories });
  const departments = useQuery({
    queryKey: ["admin", "departments"],
    queryFn: adminApi.departments,
  });

  const create = useMutation({
    mutationFn: () =>
      adminApi.createCategory({
        name: form.name,
        code: form.code,
        department_id: Number(form.department_id),
      }),
    onSuccess: () => {
      setNotice("Category created.");
      setForm({ name: "", code: "", department_id: "" });
      void queryClient.invalidateQueries({ queryKey: ["admin", "categories"] });
    },
    onError: (error: unknown) =>
      setNotice(error instanceof ApiError ? error.message : "Create failed."),
  });
  const update = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      adminApi.updateCategory(id, payload),
    onSuccess: () => {
      setNotice("Category updated.");
      void queryClient.invalidateQueries({ queryKey: ["admin", "categories"] });
    },
    onError: (error: unknown) =>
      setNotice(error instanceof ApiError ? error.message : "Update failed."),
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">Categories</h1>
      <form
        className="grid gap-3 sm:grid-cols-4"
        onSubmit={(event) => {
          event.preventDefault();
          create.mutate();
        }}
      >
        <FormField label="Name" htmlFor="cat-name">
          <input
            id="cat-name"
            className={inputClass}
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        </FormField>
        <FormField label="Code" htmlFor="cat-code">
          <input
            id="cat-code"
            className={inputClass}
            value={form.code}
            onChange={(e) => setForm({ ...form, code: e.target.value })}
            required
          />
        </FormField>
        <FormField label="Routes to department" htmlFor="cat-dept">
          <select
            id="cat-dept"
            className={inputClass}
            value={form.department_id}
            onChange={(e) => setForm({ ...form, department_id: e.target.value })}
            required
          >
            <option value="">Choose a department</option>
            {(departments.data?.items ?? []).map((dept) => (
              <option key={dept.id} value={dept.id}>
                {dept.name}
              </option>
            ))}
          </select>
        </FormField>
        <div className="flex items-end">
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Creating…" : "Create category"}
          </Button>
        </div>
      </form>
      {notice ? (
        <p role="status" className="text-sm font-medium">
          {notice}
        </p>
      ) : null}
      {categories.isLoading ? (
        <LoadingSkeleton />
      ) : categories.error ? (
        <ErrorState
          message="We could not load categories."
          onRetry={() => void categories.refetch()}
        />
      ) : categories.data && categories.data.items.length === 0 ? (
        <EmptyState title="No categories" message="Create a category and map it to a department." />
      ) : (
        <ul className="space-y-3">
          {(categories.data?.items ?? []).map((category) => (
            <li key={category.id} className="rounded-xl border border-border bg-card p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-medium">{category.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {category.code} ·{" "}
                    {category.department?.name ?? `Department ${category.department_id}`} ·{" "}
                    {category.is_active ? "Active" : "Inactive"}
                  </p>
                  {!category.department ? (
                    <p className="text-xs font-medium text-amber-700">
                      Unmapped category: choose a department to enable routing.
                    </p>
                  ) : null}
                </div>
                <div className="flex gap-2">
                  <select
                    aria-label={`Remap ${category.name}`}
                    className="h-9 rounded-md border border-input bg-background px-2 text-sm"
                    value={category.department_id}
                    disabled={update.isPending}
                    onChange={(e) =>
                      update.mutate({
                        id: category.id,
                        payload: { department_id: Number(e.target.value) },
                      })
                    }
                  >
                    {(departments.data?.items ?? []).map((dept) => (
                      <option key={dept.id} value={dept.id}>
                        {dept.name}
                      </option>
                    ))}
                  </select>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={update.isPending}
                    onClick={() =>
                      update.mutate({
                        id: category.id,
                        payload: { is_active: !category.is_active },
                      })
                    }
                  >
                    {category.is_active ? "Deactivate" : "Activate"}
                  </Button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
