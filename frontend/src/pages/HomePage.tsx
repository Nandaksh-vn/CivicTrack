import { Link } from "react-router-dom";
import { ArrowRight, ClipboardList, MapPin, ShieldCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { homePathForRole } from "@/components/layout/navigation";
import { useAuth } from "@/hooks/useAuth";

interface Capability {
  icon: LucideIcon;
  title: string;
  description: string;
}

const capabilities: Capability[] = [
  {
    icon: ClipboardList,
    title: "Report an issue",
    description:
      "Citizens submit a category, description, location, and optional photos.",
  },
  {
    icon: MapPin,
    title: "Route to the right team",
    description:
      "Department officers accept or reject complaints and record progress.",
  },
  {
    icon: ShieldCheck,
    title: "Escalate automatically",
    description:
      "Overdue resolutions escalate after review and reach the Superintendent.",
  },
];

export default function HomePage() {
  const { user, isAuthenticated } = useAuth();
  const primaryTo = isAuthenticated ? homePathForRole(user?.role) : "/login";

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
      <section className="max-w-3xl">
        <p className="mb-4 inline-flex items-center rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary">
          Public issues, tracked to resolution
        </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          CivicTrack — your city, accountable.
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">
          CivicTrack connects citizens, department officers, and city leadership in one
          auditable workflow: submit, route, act, escalate, and resolve.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild>
            <Link to={primaryTo}>
              {isAuthenticated ? "Open your workspace" : "Sign in"}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </Button>
          {!isAuthenticated ? (
            <Button asChild variant="outline">
              <Link to="/register">Create an account</Link>
            </Button>
          ) : null}
        </div>
      </section>

      <section className="mt-16 grid gap-4 md:grid-cols-3">
        {capabilities.map((capability) => {
          const Icon = capability.icon;
          return (
            <article
              className="rounded-xl border border-border bg-card p-6 shadow-sm"
              key={capability.title}
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <h2 className="mt-5 text-base font-semibold">{capability.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {capability.description}
              </p>
            </article>
          );
        })}
      </section>
    </div>
  );
}
