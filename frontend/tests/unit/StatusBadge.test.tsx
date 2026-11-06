import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { StatusBadge } from "@/components/status/StatusBadge";

describe("StatusBadge", () => {
  it("renders label for each known status", () => {
    const cases: [string, string][] = [
      ["SUBMITTED", "Submitted"],
      ["ACCEPTED", "Accepted by department"],
      ["IN_PROGRESS", "Work in progress"],
      ["RESOLVED", "Resolved"],
      ["ESCALATED", "Escalated to Superintendent"],
      ["REJECTED", "Rejected"],
    ];
    for (const [status, expectedLabel] of cases) {
      render(<StatusBadge status={status} />);
      expect(screen.getByText(expectedLabel)).toBeInTheDocument();
    }
  });

  it("renders unknown status as passthrough label", () => {
    render(<StatusBadge status="UNKNOWN_STATUS" />);
    expect(screen.getByText("UNKNOWN STATUS")).toBeInTheDocument();
  });
});
