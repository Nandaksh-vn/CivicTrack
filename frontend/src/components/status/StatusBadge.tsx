import { statusLabel, statusMeta, type ComplaintStatus } from "@/lib/status";

export function StatusBadge({ status }: { status: string }) {
  const meta = statusMeta[status as ComplaintStatus];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${meta?.badgeClass ?? "bg-slate-100 text-slate-800"}`}
    >
      {statusLabel(status)}
    </span>
  );
}
