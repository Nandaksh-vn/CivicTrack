/** Phase 14 primitives (FE-012…FE-016): table, pagination, badge, dialog, states. */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { DataTable, type DataColumn } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/ui/pagination";
import { StatusBadge, ComplaintStatusBadge } from "@/components/ui/status-badge";

interface Row {
  id: number;
  name: string;
}

const columns: DataColumn<Row>[] = [
  { key: "id", header: "ID", render: (row) => row.id },
  { key: "name", header: "Name", render: (row) => row.name },
];

describe("DataTable", () => {
  it("renders rows with accessible headers", () => {
    render(
      <DataTable
        columns={columns}
        rows={[{ id: 1, name: "Streetlight" }]}
        rowKey={(row) => row.id}
        caption="complaints"
      />,
    );
    expect(screen.getByRole("table", { name: "complaints" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "ID" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "Streetlight" })).toBeInTheDocument();
  });

  it("renders the empty state when there is nothing to show", () => {
    render(
      <DataTable
        columns={columns}
        rows={[]}
        rowKey={(row) => row.id}
        emptyTitle="No complaints"
      />,
    );
    expect(screen.getByText("No complaints")).toBeInTheDocument();
  });

  it("renders a loading skeleton instead of an empty flash", () => {
    render(
      <DataTable
        columns={columns}
        rows={[]}
        rowKey={(row) => row.id}
        loading
      />,
    );
    expect(screen.queryByText(/no complaints/i)).not.toBeInTheDocument();
    expect(screen.getByRole("status", { name: "Loading" })).toBeInTheDocument();
  });
});

describe("Pagination", () => {
  it("disables previous on page 1 and advances on next", async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();
    render(
      <Pagination
        page={1}
        pageSize={20}
        total={100}
        totalPages={5}
        onPageChange={onPageChange}
      />,
    );
    expect(screen.getByRole("button", { name: /previous/i })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: /next/i }));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("marks the current page with aria-current", () => {
    render(
      <Pagination
        page={2}
        pageSize={20}
        total={100}
        totalPages={5}
        onPageChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Page 2" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });
});

describe("StatusBadge", () => {
  it("renders the canonical label for known statuses", () => {
    render(<ComplaintStatusBadge status="PENDING_DEPARTMENT_REVIEW" />);
    expect(screen.getByText("Pending review")).toBeInTheDocument();
  });

  it("falls back to the raw value for unknown statuses without crashing", () => {
    render(<StatusBadge label="CUSTOM" />);
    expect(screen.getByText("CUSTOM")).toBeInTheDocument();
  });
});

describe("ConfirmDialog", () => {
  it("focuses the confirm button and confirms on Enter", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        title="Delete image?"
        description="This cannot be undone."
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(screen.getByRole("button", { name: /confirm/i })).toHaveFocus();
    await user.keyboard("[Enter]");
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("cancels on Escape", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        title="Delete image?"
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );
    await user.keyboard("[Escape]");
    expect(onCancel).toHaveBeenCalled();
    expect(onConfirm).not.toHaveBeenCalled();
  });
});

describe("EmptyState and ErrorState", () => {
  it("renders empty state copy and optional action", () => {
    render(
      <EmptyState title="Nothing yet" description="Report something." action={<button>Go</button>} />,
    );
    expect(screen.getByRole("heading", { name: "Nothing yet" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Go" })).toBeInTheDocument();
  });

  it("error state announces via role=alert and supports retry", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(<ErrorState title="Failed" message="try again" onRetry={onRetry} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});

describe("FormField", () => {
  it("links the label to the control and surfaces the error with role=alert", () => {
    render(
      <FormField id="title" label="Title" required error="Title is too short">
        <Input name="title" />
      </FormField>,
    );
    const input = screen.getByLabelText(/title/i);
    expect(input).toHaveAttribute("id", "title");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute("aria-describedby", expect.stringContaining("title-error"));
    expect(screen.getByRole("alert")).toHaveTextContent("Title is too short");
  });
});
