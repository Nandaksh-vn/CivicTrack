import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { ApiError } from "@/api/client";
import { complaintsApi, departmentApi, superintendentApi } from "@/api/modules";
import { FormField, inputClass } from "@/components/forms/FormField";
import { Button } from "@/components/ui/button";
import {
  progressSchema,
  rejectSchema,
  resolveSchema,
  superintendentActionSchema,
  validateImageFiles,
} from "@/lib/validators";

function useInvalidate(id: string) {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.invalidateQueries({ queryKey: ["complaint", id] });
    void queryClient.invalidateQueries({ queryKey: ["timeline", id] });
    void queryClient.invalidateQueries({ queryKey: ["department"] });
    void queryClient.invalidateQueries({ queryKey: ["escalations"] });
    void queryClient.invalidateQueries({ queryKey: ["complaints"] });
  };
}

function ActionError({ error }: { error: unknown }) {
  if (!error) return null;
  const message =
    error instanceof ApiError && error.status === 409
      ? "This action is no longer allowed for the current status. Refresh and try again."
      : error instanceof Error
        ? error.message
        : "Action failed.";
  return (
    <p role="alert" className="text-sm font-medium text-destructive">
      {message}
    </p>
  );
}

export function AcceptRejectPanel({ id, status }: { id: string; status: string }) {
  const invalidate = useInvalidate(id);
  const [reason, setReason] = useState("");
  const [reasonError, setReasonError] = useState<string | null>(null);
  const accept = useMutation({
    mutationFn: () => departmentApi.accept(id),
    onSuccess: invalidate,
  });
  const reject = useMutation({
    mutationFn: (value: string) => departmentApi.reject(id, value),
    onSuccess: invalidate,
  });

  function submitReject() {
    const parsed = rejectSchema.safeParse({ reason });
    if (!parsed.success) {
      setReasonError(parsed.error.issues[0]?.message ?? "Invalid reason.");
      return;
    }
    setReasonError(null);
    reject.mutate(parsed.data.reason);
  }

  if (status !== "PENDING_DEPARTMENT_REVIEW") return null;
  return (
    <div className="mt-4 space-y-3 rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold">Department decision</h2>
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => accept.mutate()} disabled={accept.isPending}>
          {accept.isPending ? "Accepting…" : "Accept complaint"}
        </Button>
      </div>
      <FormField label="Rejection reason" htmlFor="reject-reason" error={reasonError ?? undefined}>
        <input
          id="reject-reason"
          className={inputClass}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        />
      </FormField>
      <Button variant="destructive" onClick={submitReject} disabled={reject.isPending}>
        {reject.isPending ? "Rejecting…" : "Reject complaint"}
      </Button>
      <ActionError error={accept.error ?? reject.error} />
    </div>
  );
}

export function ProgressPanel({ id, status }: { id: string; status: string }) {
  const invalidate = useInvalidate(id);
  const form = useForm<{ note: string; set_status?: "IN_PROGRESS" }>({
    resolver: zodResolver(progressSchema),
    mode: "onBlur",
  });
  const mutation = useMutation({
    mutationFn: (values: { note: string; set_status?: "IN_PROGRESS" }) =>
      departmentApi.progress(id, values),
    onSuccess: () => {
      invalidate();
      form.reset();
    },
  });
  if (!["ACCEPTED", "IN_PROGRESS", "ESCALATED"].includes(status)) return null;
  return (
    <form
      className="mt-4 space-y-3 rounded-lg border border-border p-4"
      onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      noValidate
    >
      <h2 className="text-sm font-semibold">Progress update</h2>
      {status === "ESCALATED" ? (
        <p className="text-xs text-muted-foreground">
          This complaint is escalated. Progress notes are allowed; the status stays ESCALATED.
        </p>
      ) : null}
      <FormField label="Note" htmlFor="progress-note" error={form.formState.errors.note?.message}>
        <textarea
          id="progress-note"
          rows={3}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          {...form.register("note")}
        />
      </FormField>
      {status === "ACCEPTED" ? (
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" value="IN_PROGRESS" {...form.register("set_status")} />
          Move to IN_PROGRESS
        </label>
      ) : null}
      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Posting…" : "Post progress"}
      </Button>
      <ActionError error={mutation.error} />
    </form>
  );
}

export function AssignPanel({ id }: { id: string }) {
  const invalidate = useInvalidate(id);
  const [assignee, setAssignee] = useState("");
  const mutation = useMutation({
    mutationFn: () => departmentApi.assign(id, Number(assignee)),
    onSuccess: invalidate,
  });
  return (
    <div className="mt-4 space-y-3 rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold">Assign to staff</h2>
      <FormField label="Staff user ID" htmlFor="assignee">
        <input
          id="assignee"
          type="number"
          min={1}
          className={inputClass}
          value={assignee}
          onChange={(event) => setAssignee(event.target.value)}
        />
      </FormField>
      <Button
        variant="outline"
        disabled={mutation.isPending || !assignee}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? "Assigning…" : "Assign"}
      </Button>
      <ActionError error={mutation.error} />
    </div>
  );
}

export function EvidencePanel({ id }: { id: string }) {
  const invalidate = useInvalidate(id);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const mutation = useMutation({
    mutationFn: () => {
      const form = new FormData();
      form.set("kind", "PROGRESS");
      for (const file of files) form.append("images", file);
      return complaintsApi.uploadEvidence(id, form);
    },
    onSuccess: invalidate,
  });
  return (
    <div className="mt-4 space-y-3 rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold">Upload evidence</h2>
      <FormField label="Evidence images (1–3)" htmlFor="evidence" error={error ?? undefined}>
        <input
          id="evidence"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          className={inputClass}
          onChange={(event) => {
            const selected = Array.from(event.target.files ?? []);
            const problem = validateImageFiles(selected);
            setError(problem);
            if (!problem) setFiles(selected);
          }}
        />
      </FormField>
      <Button
        variant="outline"
        disabled={mutation.isPending || files.length === 0}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? "Uploading…" : "Upload evidence"}
      </Button>
      <ActionError error={mutation.error} />
    </div>
  );
}

export function ResolvePanel({
  id,
  onResolve,
}: {
  id: string;
  onResolve?: (note: string) => Promise<unknown>;
}) {
  const invalidate = useInvalidate(id);
  const form = useForm<{ resolution_note: string }>({
    resolver: zodResolver(resolveSchema),
    mode: "onBlur",
  });
  const mutation = useMutation({
    mutationFn: (values: { resolution_note: string }) =>
      onResolve
        ? onResolve(values.resolution_note)
        : departmentApi.resolve(id, values.resolution_note),
    onSuccess: invalidate,
  });
  return (
    <form
      className="mt-4 space-y-3 rounded-lg border border-border p-4"
      onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      noValidate
    >
      <h2 className="text-sm font-semibold">Resolve complaint</h2>
      <FormField
        label="Resolution note"
        htmlFor="resolution-note"
        error={form.formState.errors.resolution_note?.message}
      >
        <textarea
          id="resolution-note"
          rows={3}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          {...form.register("resolution_note")}
        />
      </FormField>
      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Resolving…" : "Resolve complaint"}
      </Button>
      <ActionError error={mutation.error} />
    </form>
  );
}

export function SuperintendentActionPanel({ id }: { id: string }) {
  const invalidate = useInvalidate(id);
  const form = useForm<{
    action_type: "INSTRUCTION" | "FOLLOW_UP" | "REASSIGN" | "NOTE";
    note: string;
    directed_department_id?: number;
  }>({
    resolver: zodResolver(superintendentActionSchema),
    mode: "onBlur",
    defaultValues: { action_type: "INSTRUCTION" },
  });
  const mutation = useMutation({
    mutationFn: (values: { action_type: string; note: string; directed_department_id?: number }) =>
      superintendentApi.action(id, values),
    onSuccess: () => {
      invalidate();
      form.reset({ action_type: "INSTRUCTION" });
    },
  });
  return (
    <form
      className="mt-4 space-y-3 rounded-lg border border-border p-4"
      onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      noValidate
    >
      <h2 className="text-sm font-semibold">Record supervisory action</h2>
      <FormField
        label="Action type"
        htmlFor="action-type"
        error={form.formState.errors.action_type?.message}
      >
        <select id="action-type" className={inputClass} {...form.register("action_type")}>
          <option value="INSTRUCTION">Instruction</option>
          <option value="FOLLOW_UP">Follow-up</option>
          <option value="REASSIGN">Reassign</option>
          <option value="NOTE">Note</option>
        </select>
      </FormField>
      <FormField label="Note" htmlFor="action-note" error={form.formState.errors.note?.message}>
        <textarea
          id="action-note"
          rows={3}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          {...form.register("note")}
        />
      </FormField>
      <FormField
        label="Directed department ID (optional)"
        htmlFor="directed-department"
        error={form.formState.errors.directed_department_id?.message}
      >
        <input
          id="directed-department"
          type="number"
          min={1}
          className={inputClass}
          {...form.register("directed_department_id")}
        />
      </FormField>
      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Recording…" : "Record action"}
      </Button>
      <ActionError error={mutation.error} />
    </form>
  );
}
