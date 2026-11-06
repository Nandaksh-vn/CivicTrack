import { useContext } from "react";

import { ToastContext, type ToastContextValue } from "@/components/ui/toast-context";

/** Access the toast system; throws outside `ToastProvider`. */
export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
