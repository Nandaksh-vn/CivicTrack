import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/api/client";

const NON_RETRYABLE = new Set([400, 401, 403, 404, 409, 422]);

/** Shared query client: browser-like retry policy, never retry authz failures. */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        staleTime: 30_000,
        gcTime: 5 * 60_000,
        retry: (failureCount, error) => {
          if (error instanceof ApiError && NON_RETRYABLE.has(error.status)) {
            return false;
          }
          return failureCount < 1;
        },
      },
      mutations: {
        retry: false,
      },
    },
  });
}
