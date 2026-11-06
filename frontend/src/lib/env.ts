/**
 * Typed environment access. Everything the app reads from `import.meta.env`
 * goes through this module so missing/invalid configuration fails loudly in
 * one place instead of being sprinkled across features.
 */

const raw = import.meta.env as Record<string, string | undefined>;

export const env = {
  apiBaseUrl: raw.VITE_API_BASE_URL ?? "/api/v1",
  isProd: raw.PROD === "true" || raw.MODE === "production",
} as const;

export type Env = typeof env;
