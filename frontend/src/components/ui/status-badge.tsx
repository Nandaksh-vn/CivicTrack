import { cn } from "@/lib/utils";
import { getComplaintStatusMeta, getPriorityMeta } from "@/lib/status-meta";

export interface StatusBadgeProps {
  /** Pre-resolved label; useful for non-complaint statuses. */
  label: string;
  className?: string;
}

/** Compact coloured badge. Callers own the label via the status-meta map. */
export function StatusBadge({ label, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        "border-slate-200 bg-slate-100 text-slate-800",
        className,
      )}
    >
      {label}
    </span>
  );
}

export function ComplaintStatusBadge({ status }: { status: string }) {
  const meta = getComplaintStatusMeta(status);
  return <StatusBadge label={meta.label} className={meta.className} />;
}

export function PriorityBadge({ priority }: { priority: string }) {
  const meta = getPriorityMeta(priority);
  return <StatusBadge label={meta.label} className={meta.className} />;
}
