import type { TimelineEvent } from "@/api/types";
import { formatDateTime, formatOverdue, statusLabel } from "@/lib/status";

export function TimelineView({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-muted-foreground">No timeline events yet.</p>;
  }
  return (
    <ol className="space-y-4">
      {events.map((event) => (
        <li key={event.id} className="rounded-lg border border-border p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <strong className="text-sm">{event.event_type.replaceAll("_", " ")}</strong>
            <time className="text-xs text-muted-foreground">
              {formatDateTime(event.created_at)}
            </time>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {event.actor.display_name} ({event.actor.role})
            {event.from_status || event.to_status ? (
              <>
                {" "}
                — {event.from_status ? statusLabel(event.from_status) : "—"} →{" "}
                {event.to_status ? statusLabel(event.to_status) : "—"}
              </>
            ) : null}
            {event.action_type ? ` · ${event.action_type}` : ""}
            {event.overdue_seconds ? ` · ${formatOverdue(event.overdue_seconds)}` : ""}
          </p>
          {event.note ? <p className="mt-2 text-sm">{event.note}</p> : null}
          {event.image ? (
            <img
              src={event.image.url}
              alt="Timeline evidence"
              className="mt-2 max-h-40 rounded border border-border object-cover"
            />
          ) : null}
        </li>
      ))}
    </ol>
  );
}
