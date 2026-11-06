import { useEffect } from "react";
import { NavLink } from "react-router-dom";
import { ShieldCheck, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { navForRole } from "@/components/layout/navigation";
import { useAuth } from "@/features/auth/AuthProvider";
import { cn } from "@/lib/utils";
import type { Role } from "@/types";

const linkBase =
  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return cn(
    linkBase,
    isActive
      ? "bg-primary text-primary-foreground shadow"
      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
  );
}

export interface SidebarProps {
  /** Mobile drawer visibility; ignored on desktop where the rail is static. */
  open: boolean;
  onClose: () => void;
}

/**
 * Role-aware primary navigation. Desktop shows a static rail; on small
 * screens the same content renders inside an overlay driven by the topbar
 * hamburger. Escape closes the overlay and focus returns to the trigger.
 */
export function Sidebar({ open, onClose }: SidebarProps) {
  const { user } = useAuth();
  const items = navForRole(user?.role as Role | null | undefined);

  useEffect(() => {
    if (!open) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }
    }
    document.addEventListener("keydown", handleKeyDown, true);
    return () => document.removeEventListener("keydown", handleKeyDown, true);
  }, [open, onClose]);

  const nav = (
    <nav aria-label="Primary navigation" className="flex flex-col gap-1 p-4">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            className={navLinkClass}
            onClick={onClose}
          >
            <Icon aria-hidden="true" className="h-4 w-4 shrink-0" />
            {item.label}
          </NavLink>
        );
      })}
    </nav>
  );

  const brand = (
    <div className="flex h-16 shrink-0 items-center justify-between border-b border-border px-4">
      <span className="flex items-center gap-2 font-semibold tracking-tight">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <ShieldCheck className="h-4 w-4" aria-hidden="true" />
        </span>
        CivicTrack
      </span>
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={onClose}
        aria-label="Close navigation"
      >
        <X aria-hidden="true" className="h-5 w-5" />
      </Button>
    </div>
  );

  return (
    <>
      {/* Desktop rail */}
      <aside className="hidden h-full w-64 shrink-0 flex-col border-r border-border bg-card md:flex">
        {brand}
        <div className="flex-1 overflow-y-auto">{nav}</div>
        <p className="border-t border-border px-4 py-3 text-xs leading-5 text-muted-foreground">
          Community issues, tracked openly from report to resolution.
        </p>
      </aside>

      {/* Mobile overlay */}
      {open ? (
        <div className="fixed inset-0 z-40 md:hidden" role="presentation">
          <div
            className="absolute inset-0 bg-black/50"
            aria-hidden="true"
            onClick={onClose}
          />
          <aside className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col border-r border-border bg-card shadow-xl">
            {brand}
            <div className="flex-1 overflow-y-auto">{nav}</div>
          </aside>
        </div>
      ) : null}
    </>
  );
}
