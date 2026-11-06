import { useQuery } from "@tanstack/react-query";

import { complaintsApi } from "@/api/modules";
import type { ComplaintDetail } from "@/api/types";
import { StatusBadge } from "@/components/status/StatusBadge";
import { TimelineView } from "@/components/complaints/TimelineView";
import { ErrorState, LoadingSkeleton } from "@/components/states/PageStates";
import { formatDateTime, formatOverdue } from "@/lib/status";

export function ComplaintDetailView({
  id,
  detail: initial,
  children,
}: {
  id: string;
  detail?: ComplaintDetail;
  children?: React.ReactNode;
}) {
  const query = useQuery({
    queryKey: ["complaint", id],
    queryFn: () => complaintsApi.detail(id),
    enabled: !initial,
  });
  const timeline = useQuery({
    queryKey: ["timeline", id],
    queryFn: () => complaintsApi.timeline(id),
  });

  const detail = initial ?? query.data;
  if (query.isLoading) return <LoadingSkeleton label="Loading complaint…" />;
  if (query.error || !detail) {
    return (
      <ErrorState
        message="We could not load this complaint. It may not exist or you may not have access to it."
        onRetry={() => void query.refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <header className="rounded-xl border border-border bg-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm text-muted-foreground">{detail.complaint_number}</p>
            <h1 className="text-2xl font-semibold tracking-tight">{detail.title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {detail.department} · {detail.category}
            </p>
          </div>
          <StatusBadge status={detail.status} />
        </div>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-muted-foreground">Submitted</dt>
            <dd>{formatDateTime(detail.submitted_at)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Resolution deadline</dt>
            <dd>{formatDateTime(detail.resolution_due_at ?? null)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Overdue</dt>
            <dd>
              {detail.is_overdue || detail.overdue
                ? formatOverdue(detail.overdue_seconds ?? 0)
                : "Not overdue"}
            </dd>
          </div>
        </dl>
        {children}
      </header>

      <section className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold">Description</h2>
        <p className="mt-2 text-sm leading-6">{detail.description}</p>
        {detail.location?.text ? (
          <p className="mt-2 text-sm text-muted-foreground">Location: {detail.location.text}</p>
        ) : null}
      </section>

      {detail.resolution ? (
        <section className="rounded-xl border border-border bg-card p-6">
          <h2 className="text-base font-semibold">Resolution</h2>
          <p className="mt-2 text-sm">{detail.resolution.note ?? "—"}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Resolved {formatDateTime(detail.resolution.resolved_at)}
            {detail.resolution.resolved_by ? ` by ${detail.resolution.resolved_by.full_name}` : ""}
          </p>
        </section>
      ) : null}

      <section className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold">Evidence images</h2>
        {detail.images.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">No images attached.</p>
        ) : (
          <ul className="mt-3 grid gap-3 sm:grid-cols-3">
            {detail.images.map((image) => (
              <li key={image.id}>
                <img
                  src={image.url}
                  alt={`${image.kind} evidence`}
                  className="max-h-48 w-full rounded border border-border object-cover"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  {image.kind} · {image.mime_type}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold">Timeline</h2>
        <div className="mt-3">
          {timeline.isLoading ? (
            <LoadingSkeleton />
          ) : timeline.error ? (
            <ErrorState
              message="We could not load the timeline."
              onRetry={() => void timeline.refetch()}
            />
          ) : (
            <TimelineView events={timeline.data?.items ?? []} />
          )}
        </div>
      </section>
    </div>
  );
}
