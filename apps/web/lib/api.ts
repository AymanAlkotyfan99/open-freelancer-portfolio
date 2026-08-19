export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { ...init, credentials: "include", headers: { "Content-Type": "application/json", ...init?.headers } });
  if (!response.ok) throw new Error(response.status === 429 ? "Please wait before trying again." : "We could not complete your request.");
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
