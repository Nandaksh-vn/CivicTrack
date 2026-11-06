import { useEffect, useState } from "react";

import { formatDateTime, formatOverdue } from "@/lib/status";

export function OverdueTimer({
  overdueSeconds,
  dueAt,
}: {
  overdueSeconds: number | null;
  dueAt: string | null;
}) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);
  const due = dueAt ? new Date(dueAt).getTime() : null;
  const liveSeconds = due !== null ? Math.max(0, Math.floor((now - due) / 1000)) : overdueSeconds;
  return (
    <div className="mt-4 rounded-lg border border-orange-200 bg-orange-50 p-4 text-sm">
      <p className="font-medium">{formatOverdue(liveSeconds)}</p>
      <p className="mt-1 text-muted-foreground">Resolution deadline: {formatDateTime(dueAt)}</p>
    </div>
  );
}
