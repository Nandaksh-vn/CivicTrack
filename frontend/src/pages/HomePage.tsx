import type { LucideIcon } from "lucide-react";
import { ArrowRight, ClipboardList, MapPin, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

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
      "Overdue resolutions escalate after seven days and reach the Superintendent.",
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-16 sm:py-24">
      <section className="max-w-3xl">
        <p className="mb-4 inline-flex items-center rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary">
          Repository and tooling baseline
        </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Public issues, tracked to resolution.
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">
          CivicTrack connects citizens, department officers, and city leadership
          in one auditable workflow: submit, route, act, escalate, and resolve.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild>
            <Link to="/">
              Explore the shell
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </Button>
          <Button asChild variant="outline">
            <a href="/health">API health</a>
          </Button>
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
              <h2 className="mt-5 text-base font-semibold">
                {capability.title}
              </h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {capability.description}
              </p>
            </article>
          );
        })}
      </section>

      <section className="mt-12 rounded-xl border border-border bg-muted/40 p-6">
        <h2 className="text-sm font-semibold">What this phase proves</h2>
        <ul className="mt-3 grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
          <li>One-command Docker Compose startup</li>
          <li>FastAPI health and readiness probes</li>
          <li>React, Vite, TypeScript, and Tailwind baseline</li>
          <li>Lint, typecheck, and test wiring for CI</li>
        </ul>
      </section>
    </div>
  );
}
