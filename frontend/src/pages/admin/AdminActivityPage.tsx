import { useQuery } from "@tanstack/react-query";

import { adminApi } from "@/api/modules";
import { TimelineView } from "@/components/complaints/TimelineView";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/states/PageStates";
import { DEMO_ESCALATION_LABEL, isDemoEscalationEnabled } from "@/lib/status";

export default function AdminActivityPage() {
  const activity = useQuery({ queryKey: ["admin", "activity"], queryFn: adminApi.activity });
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">Activity</h1>
      {(activity.data?.demo_mode ?? isDemoEscalationEnabled()) ? (
        <p className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900">
          {DEMO_ESCALATION_LABEL}
        </p>
      ) : null}
      {activity.isLoading ? (
        <LoadingSkeleton />
      ) : activity.error ? (
        <ErrorState message="We could not load activity." onRetry={() => void activity.refetch()} />
      ) : activity.data && Object.keys(activity.data.by_status ?? {}).length === 0 ? (
        <EmptyState
          title="No activity yet"
          message="Counts and recent events will appear here once complaints are submitted."
        />
      ) : (
        <>
          <dl className="grid gap-3 sm:grid-cols-4">
            {Object.entries(activity.data?.by_status ?? {}).map(([key, value]) => (
              <div key={key} className="rounded-xl border border-border bg-card p-4">
                <dt className="text-xs text-muted-foreground">{key.replaceAll("_", " ")}</dt>
                <dd className="text-xl font-semibold">{value}</dd>
              </div>
            ))}
          </dl>
          <section>
            <h2 className="text-base font-semibold">Recent events</h2>
            <div className="mt-3">
              <TimelineView events={activity.data?.recent_events ?? []} />
            </div>
          </section>
        </>
      )}
    </div>
  );
}
