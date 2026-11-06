import { createContext } from "react";

export type ToastVariant = "default" | "success" | "destructive" | "info";

export interface ToastInput {
  title: string;
  description?: string;
  variant?: ToastVariant;
}

export interface ToastItem extends ToastInput {
  id: string;
}

export interface ToastContextValue {
  toasts: ToastItem[];
  toast: (input: ToastInput) => string;
  dismiss: (id: string) => void;
}

export const ToastContext = createContext<ToastContextValue | undefined>(undefined);
