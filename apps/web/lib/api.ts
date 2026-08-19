export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const AUTH_EXPIRED_EVENT = "portfolio:auth-expired";

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

let refreshRequest: Promise<boolean> | null = null;

function request(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  if (init?.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers,
  });
}

async function refreshSession(): Promise<boolean> {
  if (!refreshRequest) {
    refreshRequest = request("/auth/refresh", { method: "POST" })
      .then((response) => response.ok)
      .catch(() => false)
      .finally(() => { refreshRequest = null; });
  }
  return refreshRequest;
}

function notifyAuthExpired(): void {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
}

async function errorMessage(response: Response): Promise<string> {
  if (response.status === 429) return "Please wait before trying again.";

  try {
    const payload = await response.clone().json() as {
      detail?: string | Array<{ loc?: Array<string | number>; msg?: string }>;
      message?: string;
    };
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail)) {
      const details = payload.detail
        .map((issue) => {
          const field = issue.loc?.filter((part) => part !== "body").join(".");
          return [field, issue.msg].filter(Boolean).join(": ");
        })
        .filter(Boolean)
        .join(" ");
      if (details) return details;
    }
    if (typeof payload.message === "string") return payload.message;
  } catch {
    // The API may return an empty or non-JSON error response.
  }

  return "We could not complete your request.";
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let response = await request(path, init);
  if (response.status === 401 && path !== "/auth/login") {
    if (await refreshSession()) response = await request(path, init);
    if (response.status === 401) notifyAuthExpired();
  }
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
