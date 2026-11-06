import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { departmentApi } from "@/api/modules";
import { Pagination } from "@/components/layout/Pagination";
import { StatusBadge } from "@/components/status/StatusBadge";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/states/PageStates";
import { formatDateTime, formatOverdue } from "@/lib/status";

export default function DepartmentQueuePage() {
  const [page, setPage] = useState(1);
  const queue = useQuery({
    queryKey: ["department", "complaints", page],
    queryFn: () => departmentApi.queue({ page, page_size: 20 }),
  });
  const summary = useQuery({
    queryKey: ["department", "summary"],
    queryFn: departmentApi.summary,
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">Department Queue</h1>
      {summary.data ? (
        <p className="text-sm text-muted-foreground">
          Open: {summary.data.open ?? 0} · Overdue: {summary.data.overdue ?? 0} · Escalated:{" "}
          {summary.data.escalated ?? 0}
        </p>
      ) : null}

      {queue.isLoading ? (
        <LoadingSkeleton label="Loading department queue…" />
      ) : queue.error ? (
        <ErrorState
          message="We could not load the department queue."
          onRetry={() => void queue.refetch()}
        />
      ) : queue.data && queue.data.items.length === 0 ? (
        <EmptyState
          title="No complaints in your queue"
          message="Complaints routed to your department will appear here."
        />
      ) : (
        <>
          <ul className="space-y-3">
            {(queue.data?.items ?? []).map((complaint) => (
              <li key={complaint.id}>
                <Link
                  to={`/department/complaints/${complaint.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-4 hover:bg-accent/50"
                >
                  <div>
                    <p className="text-sm text-muted-foreground">
                      {complaint.complaint_number} · {complaint.category}
                    </p>
                    <p className="font-medium">{complaint.title}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Submitted {formatDateTime(complaint.submitted_at)}
                      {complaint.is_overdue || complaint.overdue
                        ? ` · ${formatOverdue(complaint.overdue_seconds ?? 0)}`
                        : ""}
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
