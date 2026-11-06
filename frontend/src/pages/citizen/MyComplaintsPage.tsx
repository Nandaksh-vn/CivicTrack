import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { categoriesApi, complaintsApi } from "@/api/modules";
import { Pagination } from "@/components/layout/Pagination";
import { StatusBadge } from "@/components/status/StatusBadge";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/states/PageStates";
import { Button } from "@/components/ui/button";
import { formatDateTime, formatOverdue } from "@/lib/status";

export default function MyComplaintsPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const categories = useQuery({ queryKey: ["categories"], queryFn: categoriesApi.list });
  const complaints = useQuery({
    queryKey: ["complaints", page, status, categoryId],
    queryFn: () =>
      complaintsApi.list({
        page,
        page_size: 20,
        status: status || undefined,
        category_id: categoryId || undefined,
      }),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">My Complaints</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Only complaints you submitted are listed here.
          </p>
        </div>
        <Button asChild>
          <Link to="/complaints/new">Report a Problem</Link>
        </Button>
      </div>

      <form
        className="flex flex-wrap gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          setPage(1);
        }}
        aria-label="Filter complaints"
      >
        <label className="space-y-1 text-sm">
          <span className="font-medium">Status</span>
          <select
            aria-label="Status filter"
            className="flex h-10 rounded-md border border-input bg-background px-3"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All statuses</option>
            {[
              "SUBMITTED",
              "PENDING_DEPARTMENT_REVIEW",
              "ACCEPTED",
              "IN_PROGRESS",
              "REJECTED",
              "ESCALATED",
              "RESOLVED",
            ].map((value) => (
              <option key={value} value={value}>
                {value.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium">Category</span>
          <select
            aria-label="Category filter"
            className="flex h-10 rounded-md border border-input bg-background px-3"
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value)}
          >
            <option value="">All categories</option>
            {(categories.data?.items ?? []).map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
        <Button type="submit" variant="outline" className="self-end">
          Apply filters
        </Button>
      </form>

      {complaints.isLoading ? (
        <LoadingSkeleton label="Loading your complaints…" />
      ) : complaints.error ? (
        <ErrorState
          message="We could not load your complaints."
          onRetry={() => void complaints.refetch()}
        />
      ) : complaints.data && complaints.data.items.length === 0 ? (
        <EmptyState
          title="You have not submitted any complaints yet"
          message="When you report an issue, its tracking number and status will appear here."
          action={
            <Button asChild>
              <Link to="/complaints/new">Report your first problem</Link>
            </Button>
          }
        />
      ) : (
        <>
          <ul className="space-y-3">
            {(complaints.data?.items ?? []).map((complaint) => (
              <li key={complaint.id}>
                <Link
                  to={`/complaints/${complaint.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-4 hover:bg-accent/50"
                >
                  <div>
                    <p className="text-sm text-muted-foreground">{complaint.complaint_number}</p>
                    <p className="font-medium">{complaint.title}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {complaint.category} · {complaint.department} · Submitted{" "}
                      {formatDateTime(complaint.submitted_at)}
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
            page={complaints.data?.page ?? page}
            totalPages={complaints.data?.total_pages ?? 1}
            onPage={setPage}
          />
        </>
      )}
    </div>
  );
}
