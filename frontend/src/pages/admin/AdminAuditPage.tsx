import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { adminApi } from "@/api/modules";
import { Pagination } from "@/components/layout/Pagination";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/states/PageStates";
import { Button } from "@/components/ui/button";
import { formatDateTime } from "@/lib/status";

export default function AdminAuditPage() {
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);
  const logs = useQuery({
    queryKey: ["admin", "audit", page, action, entityType],
    queryFn: () =>
      adminApi.auditLogs({
        page,
        page_size: 20,
        action: action || undefined,
        entity_type: entityType || undefined,
      }),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">Audit Log</h1>
      <form
        className="flex flex-wrap gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          setPage(1);
          void logs.refetch();
        }}
      >
        <label className="space-y-1 text-sm">
          <span className="font-medium">Action</span>
          <input
            aria-label="Action filter"
            className="flex h-10 rounded-md border border-input bg-background px-3"
            value={action}
            onChange={(e) => setAction(e.target.value)}
            placeholder="e.g. COMPLAINT_ACCEPTED"
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium">Entity type</span>
          <input
            aria-label="Entity type filter"
            className="flex h-10 rounded-md border border-input bg-background px-3"
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            placeholder="e.g. complaint"
          />
        </label>
        <Button type="submit" variant="outline" className="self-end">
          Apply filters
        </Button>
      </form>
      {logs.isLoading ? (
        <LoadingSkeleton />
      ) : logs.error ? (
        <ErrorState
          message="We could not load the audit log."
          onRetry={() => void logs.refetch()}
        />
      ) : logs.data && logs.data.items.length === 0 ? (
        <EmptyState title="No matching events" message="Try widening the filters." />
      ) : (
        <>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted-foreground">
                <th className="py-2 pr-4">Time</th>
                <th className="py-2 pr-4">Action</th>
                <th className="py-2 pr-4">Entity</th>
                <th className="py-2">Details</th>
              </tr>
            </thead>
            <tbody>
              {(logs.data?.items ?? []).map((log) => (
                <tr key={log.id} className="border-t border-border align-top">
                  <td className="py-2 pr-4">{formatDateTime(log.created_at)}</td>
                  <td className="py-2 pr-4">{log.action}</td>
                  <td className="py-2 pr-4">
                    {log.entity_type} #{log.entity_id ?? "—"}
                  </td>
                  <td className="py-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setExpanded(expanded === log.id ? null : log.id)}
                    >
                      {expanded === log.id ? "Hide" : "Show"}
                    </Button>
                    {expanded === log.id ? (
                      <pre className="mt-2 max-w-md overflow-auto rounded bg-muted p-2 text-xs">
                        {JSON.stringify(log.meta ?? {}, null, 2)}
                      </pre>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination
            page={logs.data?.page ?? page}
            totalPages={logs.data?.total_pages ?? 1}
            onPage={setPage}
          />
        </>
      )}
    </div>
  );
}
