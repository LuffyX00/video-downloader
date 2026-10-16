const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export class ApiError extends Error {
  constructor(message, status, code) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export async function request(path, { method = "GET", body, signal } = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      signal,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check that the backend is running.", 0, "network");
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    /* non-JSON body */
  }

  if (!response.ok) {
    const message =
      data?.error?.message ||
      (typeof data?.detail === "string" ? data.detail : null) ||
      "Something went wrong. Please try again.";
    throw new ApiError(message, response.status, data?.error?.code);
  }
  return data;
}

export const apiUrl = (path) => `${BASE_URL}${path}`;
