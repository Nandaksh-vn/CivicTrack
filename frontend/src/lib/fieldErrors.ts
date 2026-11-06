import { ApiError } from "@/api/client";

/** Extract server 422 field errors (`details.fields[]`) into a flat map. */
export function fieldErrorsFrom(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError)) return {};
  const details = error.details as { fields?: { field: string; message: string }[] } | undefined;
  const out: Record<string, string> = {};
  for (const field of details?.fields ?? []) out[field.field] = field.message;
  return out;
}
