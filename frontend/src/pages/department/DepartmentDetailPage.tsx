import { useParams } from "react-router-dom";

import {
  AcceptRejectPanel,
  AssignPanel,
  EvidencePanel,
  ProgressPanel,
  ResolvePanel,
} from "@/components/complaints/ComplaintActions";
import { ComplaintDetailView } from "@/components/complaints/ComplaintDetailView";
import { useQuery } from "@tanstack/react-query";

import { complaintsApi } from "@/api/modules";

export default function DepartmentDetailPage() {
  const { id = "" } = useParams();
  const detail = useQuery({ queryKey: ["complaint", id], queryFn: () => complaintsApi.detail(id) });
  const status = detail.data?.status ?? "";
  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <ComplaintDetailView id={id}>
        <AcceptRejectPanel id={id} status={status} />
        <AssignPanel id={id} />
        <ProgressPanel id={id} status={status} />
        <EvidencePanel id={id} />
        {["ACCEPTED", "IN_PROGRESS", "ESCALATED"].includes(status) ? (
          <ResolvePanel id={id} />
        ) : null}
      </ComplaintDetailView>
    </div>
  );
}
