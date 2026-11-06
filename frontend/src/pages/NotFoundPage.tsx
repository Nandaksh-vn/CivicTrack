import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col items-start px-6 py-24">
      <p className="text-sm font-medium text-primary">404</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">
        That page does not exist.
      </h1>
      <p className="mt-3 text-muted-foreground">
        The route may move as the application grows through later phases.
      </p>
      <Button asChild className="mt-8">
        <Link to="/">Back to CivicTrack</Link>
      </Button>
    </div>
  );
}
