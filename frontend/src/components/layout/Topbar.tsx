import { Link } from "react-router-dom";
import { LogOut, Menu, ShieldCheck, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { homePathForRole } from "@/components/layout/navigation";
import { useAuth } from "@/features/auth/AuthProvider";
import { roleLabels } from "@/lib/status-meta";

export interface TopbarProps {
  onOpenNavigation: () => void;
}

/** Sticky top bar: skip link, mobile nav trigger, identity and logout. */
export function Topbar({ onOpenNavigation }: TopbarProps) {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between gap-2 border-b border-border bg-background/95 px-4 backdrop-blur sm:px-6">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-primary-foreground"
      >
        Skip to main content
      </a>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={onOpenNavigation}
          aria-label="Open navigation"
          aria-expanded={false}
        >
          <Menu aria-hidden="true" className="h-6 w-6" />
        </Button>
        <Link
          to={homePathForRole(user?.role)}
          className="flex items-center gap-2 font-semibold tracking-tight md:hidden"
        >
          <ShieldCheck aria-hidden="true" className="h-5 w-5 text-primary" />
          CivicTrack
        </Link>
      </div>

      <div className="flex items-center gap-2 sm:gap-4">
        {user ? (
          <>
            <div className="hidden flex-col items-end leading-tight sm:flex">
              <span className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
                <UserRound aria-hidden="true" className="h-4 w-4 text-muted-foreground" />
                {user.full_name}
              </span>
              <span className="text-xs text-muted-foreground">
                {roleLabels[user.role as keyof typeof roleLabels]}
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void logout()}
              aria-label="Log out"
            >
              <LogOut aria-hidden="true" className="h-4 w-4" />
              <span className="hidden sm:inline">Log out</span>
            </Button>
          </>
        ) : null}
      </div>
    </header>
  );
}
