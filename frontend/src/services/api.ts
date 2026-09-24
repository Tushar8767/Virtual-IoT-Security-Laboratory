/**
 * API Service — Phase 0
 *
 * Base HTTP client for backend API communication.
 * Full implementation in Phase 5.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error ${response.status}: ${error}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
};

// Health check
export const getHealth = () =>
  api.get<{ status: string; version: string; services: Record<string, unknown> }>('/api/health');

// Lab status
export const getLabStatus = () =>
  api.get<{ lab_status: string; services: Record<string, unknown> }>('/api/lab/status');
