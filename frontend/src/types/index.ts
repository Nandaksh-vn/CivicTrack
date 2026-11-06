/** Shared frontend types are exported from this module. */
export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
};
