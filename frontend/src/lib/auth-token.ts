/**
 * Single source of truth for the session token.
 *
 * The token lives in `sessionStorage` under `civictrack.token` so a tab
 * close discards it; it is never written to `localStorage`. The API client
 * reads the same key, so the two cannot drift apart.
 */

export const TOKEN_STORAGE_KEY = "civictrack.token";

type Listener = (token: string | null) => void;

const listeners = new Set<Listener>();

function storageAvailable(): boolean {
  try {
    return typeof window !== "undefined" && Boolean(window.sessionStorage);
  } catch {
    return false;
  }
}

export function getToken(): string | null {
  if (!storageAvailable()) {
    return null;
  }
  return window.sessionStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string): void {
  if (storageAvailable()) {
    window.sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  }
  notify(token);
}

export function clearToken(): void {
  if (storageAvailable()) {
    window.sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  }
  notify(null);
}

export function subscribeToToken(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function notify(token: string | null): void {
  for (const listener of listeners) {
    listener(token);
  }
}
