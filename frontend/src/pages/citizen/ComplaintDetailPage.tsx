import { useParams } from "react-router-dom";

import { ComplaintDetailView } from "@/components/complaints/ComplaintDetailView";

export default function ComplaintDetailPage() {
  const { id = "" } = useParams();
  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <ComplaintDetailView id={id} />
    </div>
  );
}
