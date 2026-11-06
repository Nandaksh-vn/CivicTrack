import { Link, Outlet } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="border-b border-border/80 bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
          <Link
            className="flex items-center gap-2 font-semibold tracking-tight"
            to="/"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ShieldCheck className="h-4 w-4" aria-hidden="true" />
            </span>
            CivicTrack
          </Link>
          <span className="rounded-full border border-border bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
            Phase 3 skeleton
          </span>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-border/80">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-1 px-6 py-5 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <span>CivicTrack - community issues, tracked to resolution.</span>
          <span>React + Vite + FastAPI + MySQL</span>
        </div>
      </footer>
    </div>
  );
}
