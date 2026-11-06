import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { ResolvePanel, SuperintendentActionPanel } from "@/components/complaints/ComplaintActions";
import { ComplaintDetailView } from "@/components/complaints/ComplaintDetailView";
import { useQueryClient } from "@tanstack/react-query";

import { complaintsApi, superintendentApi } from "@/api/modules";

export default function EscalationDetailPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const detail = useQuery({
    queryKey: ["complaint", id],
    queryFn: () => complaintsApi.detail(id),
  });

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <ComplaintDetailView id={id}>
        <SuperintendentActionPanel id={id} />
        {detail.data && ["ESCALATED", "ACCEPTED", "IN_PROGRESS"].includes(detail.data.status) ? (
          <ResolvePanel
            id={id}
            onResolve={async (note) => {
              const result = await superintendentApi.resolve(id, note);
              void queryClient.invalidateQueries({ queryKey: ["escalations"] });
              void queryClient.invalidateQueries({ queryKey: ["escalation-summary"] });
              return result;
            }}
          />
        ) : null}
      </ComplaintDetailView>
    </div>
  );
}
