import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { notificationsApi } from "@/api/modules";
import { Pagination } from "@/components/layout/Pagination";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/states/PageStates";
import { Button } from "@/components/ui/button";
import { formatDateTime } from "@/lib/status";

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const list = useQuery({
    queryKey: ["notifications", page],
    queryFn: () => notificationsApi.list({ page, page_size: 20 }),
  });

  function invalidate() {
    void queryClient.invalidateQueries({ queryKey: ["notifications"] });
    void queryClient.invalidateQueries({ queryKey: ["unread-count"] });
  }

  const markRead = useMutation({
    mutationFn: (id: number) => notificationsApi.markRead(id),
    onSuccess: invalidate,
  });
  const markAll = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: invalidate,
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Notifications</h1>
        <Button variant="outline" onClick={() => markAll.mutate()} disabled={markAll.isPending}>
          {markAll.isPending ? "Updating…" : "Mark all read"}
        </Button>
      </div>
      {list.isLoading ? (
        <LoadingSkeleton />
      ) : list.error ? (
        <ErrorState
          message="We could not load your notifications."
          onRetry={() => void list.refetch()}
        />
      ) : list.data && list.data.items.length === 0 ? (
        <EmptyState
          title="No notifications"
          message="Updates about your complaints will appear here."
        />
      ) : (
        <>
          <ul className="space-y-3">
            {(list.data?.items ?? []).map((item) => (
              <li
                key={item.id}
                className={`rounded-xl border border-border bg-card p-4 ${item.is_read ? "opacity-70" : ""}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{item.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{item.body}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {item.complaint_number ?? ""} · {formatDateTime(item.created_at)}
                    </p>
                  </div>
                  {!item.is_read ? (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={markRead.isPending}
                      onClick={() => markRead.mutate(item.id)}
                    >
                      Mark read
                    </Button>
                  ) : (
                    <span className="text-xs text-muted-foreground">Read</span>
                  )}
                </div>
                {item.complaint_id ? (
                  <Link
                    className="mt-2 inline-block text-sm font-medium text-primary hover:underline"
                    to={`/complaints/${item.complaint_id}`}
                  >
                    View complaint
                  </Link>
                ) : null}
              </li>
            ))}
          </ul>
          <Pagination
            page={list.data?.page ?? page}
            totalPages={list.data?.total_pages ?? 1}
            onPage={setPage}
          />
        </>
      )}
    </div>
  );
}
