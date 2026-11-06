import { useQuery } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { ApiError } from "@/api/client";
import { categoriesApi, complaintsApi } from "@/api/modules";
import { FormField, inputClass } from "@/components/forms/FormField";
import { Button } from "@/components/ui/button";
import { complaintSchema, validateImageFiles, type ComplaintValues } from "@/lib/validators";

export default function NewComplaintPage() {
  const navigate = useNavigate();
  const [formError, setFormError] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [images, setImages] = useState<File[]>([]);

  const categories = useQuery({
    queryKey: ["categories"],
    queryFn: categoriesApi.list,
  });

  const form = useForm<ComplaintValues>({
    resolver: zodResolver(complaintSchema),
    defaultValues: {
      title: "",
      description: "",
      location_text: "",
      latitude: undefined,
      longitude: undefined,
    },
  });

  async function onSubmit(values: ComplaintValues) {
    setFormError(null);
    const data = new FormData();
    data.set("title", values.title);
    data.set("description", values.description);
    data.set("category_id", String(values.category_id));
    if (values.location_text) data.set("location_text", values.location_text);
    if (values.latitude !== undefined) data.set("latitude", String(values.latitude));
    if (values.longitude !== undefined) data.set("longitude", String(values.longitude));
    for (const image of images) data.append("images", image);

    try {
      const created = await complaintsApi.create(data);
      navigate(`/complaints/${created.id}`, { replace: true });
    } catch (error) {
      setFormError(
        error instanceof ApiError
          ? error.message
          : "We could not submit your complaint. Please try again.",
      );
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Report a problem</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Describe the issue, pick a category and attach up to 3 photos.
        </p>
      </div>

      <form
        className="space-y-4 rounded-xl border border-border bg-card p-6"
        onSubmit={form.handleSubmit(onSubmit)}
        noValidate
      >
        <FormField label="Title" htmlFor="title" error={form.formState.errors.title?.message}>
          <input
            id="title"
            className={inputClass}
            placeholder="Large pothole near the school gate"
            {...form.register("title")}
          />
        </FormField>

        <FormField
          label="Description"
          htmlFor="description"
          error={form.formState.errors.description?.message}
        >
          <textarea
            id="description"
            rows={4}
            className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="What is happening, where, and how long it has been a problem…"
            {...form.register("description")}
          />
        </FormField>

        <FormField
          label="Category"
          htmlFor="category_id"
          error={form.formState.errors.category_id?.message}
        >
          <select id="category_id" className={inputClass} {...form.register("category_id")}>
            <option value="">Choose a category…</option>
            {(categories.data?.items ?? []).map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </FormField>

        <FormField
          label="Location (optional)"
          htmlFor="location_text"
          error={form.formState.errors.location_text?.message}
        >
          <input
            id="location_text"
            className={inputClass}
            placeholder="Near Gate 2, Market Road"
            {...form.register("location_text")}
          />
        </FormField>

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            label="Latitude (optional)"
            htmlFor="latitude"
            error={form.formState.errors.latitude?.message}
          >
            <input
              id="latitude"
              type="number"
              step="any"
              className={inputClass}
              placeholder="12.971599"
              {...form.register("latitude")}
            />
          </FormField>
          <FormField
            label="Longitude (optional)"
            htmlFor="longitude"
            error={form.formState.errors.longitude?.message}
          >
            <input
              id="longitude"
              type="number"
              step="any"
              className={inputClass}
              placeholder="77.594562"
              {...form.register("longitude")}
            />
          </FormField>
        </div>

        <FormField
          label="Photos (optional, up to 3)"
          htmlFor="images"
          error={imageError ?? undefined}
        >
          <input
            id="images"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            className={inputClass}
            onChange={(event) => {
              const selected = Array.from(event.target.files ?? []);
              const problem = validateImageFiles(selected);
              setImageError(problem);
              if (!problem) setImages(selected);
            }}
          />
        </FormField>

        {formError ? (
          <p role="alert" className="text-sm font-medium text-destructive">
            {formError}
          </p>
        ) : null}

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? "Submitting…" : "Submit complaint"}
          </Button>
        </div>
      </form>
    </div>
  );
}
