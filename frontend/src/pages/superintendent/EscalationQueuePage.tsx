import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { superintendentApi } from "@/api/modules";
import { Pagination } from "@/components/layout/Pagination";
import { StatusBadge } from "@/components/status/StatusBadge";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/states/PageStates";
import { formatDateTime, formatOverdue } from "@/lib/status";

export default function EscalationQueuePage() {
  const [page, setPage] = useState(1);
  const queue = useQuery({
    queryKey: ["escalations", page],
    queryFn: () => superintendentApi.escalations({ page, page_size: 20 }),
  });
  const summary = useQuery({
    queryKey: ["escalation-summary"],
    queryFn: superintendentApi.summary,
  });

  const items = [...(queue.data?.items ?? [])].sort(
    (a, b) => (b.overdue_seconds ?? 0) - (a.overdue_seconds ?? 0),
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">Escalation Queue</h1>
      {summary.data ? (
        <p className="text-sm text-muted-foreground">
          Open escalations: {summary.data.open ?? 0} · Oldest overdue:{" "}
          {formatOverdue(summary.data.oldest_overdue_seconds ?? null)}
        </p>
      ) : null}
      {queue.isLoading ? (
        <LoadingSkeleton />
      ) : queue.error ? (
        <ErrorState message="We could not load escalations." onRetry={() => void queue.refetch()} />
      ) : items.length === 0 ? (
        <EmptyState
          title="No escalated complaints"
          message="Complaints that miss their resolution deadline will appear here, most overdue first."
        />
      ) : (
        <>
          <ul className="space-y-3">
            {items.map((complaint) => (
              <li key={complaint.id}>
                <Link
                  to={`/superintendent/${complaint.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-4 hover:bg-accent/50"
                >
                  <div>
                    <p className="text-sm text-muted-foreground">
                      {complaint.complaint_number} · {complaint.department}
                    </p>
                    <p className="font-medium">{complaint.title}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Deadline {formatDateTime(complaint.resolution_due_at ?? null)} ·{" "}
                      {formatOverdue(complaint.overdue_seconds ?? 0)}
                    </p>
                  </div>
                  <StatusBadge status={complaint.status} />
                </Link>
              </li>
            ))}
          </ul>
          <Pagination
            page={queue.data?.page ?? page}
            totalPages={queue.data?.total_pages ?? 1}
            onPage={setPage}
          />
        </>
      )}
    </div>
  );
}
