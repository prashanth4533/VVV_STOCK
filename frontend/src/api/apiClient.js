/**
 * apiClient.js
 * Centralised HTTP client for all backend requests.
 *
 * Usage:
 *   import { api } from "./apiClient";
 *   const res = await api.get("/products");
 *   const res = await api.post("/products", { brand: "…", … });
 */

// API base URL is environment-driven for production (Netlify) deployments.
// Set VITE_API_BASE_URL at build time (e.g. https://your-app.up.railway.app/api/v1).
// Falls back to the local Flask dev server when the variable is not set.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api/v1";

function getRecordCount(json) {
  if (Array.isArray(json?.data)) return json.data.length;
  if (Array.isArray(json)) return json.length;
  if (json?.meta?.total !== undefined) return json.meta.total;
  if (json?.data && typeof json.data === "object") return 1;
  return 0;
}

/**
 * Core fetch wrapper.
 * - Sets Content-Type: application/json for every request
 * - Parses JSON response
 * - Throws an enriched Error on non-2xx status
 * - Returns null for 204 No Content
 */
async function request(method, path, body) {
  const url = `${API_BASE_URL}${path}`;
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };

  if (body !== undefined) {
    opts.body = JSON.stringify(body);
  }

  let res;
  try {
    console.log("[API] URL called:", url);
    res = await fetch(url, opts);
  } catch (networkErr) {
    const err = new Error("Cannot connect to the server. Is the backend running?");
    err.code = "NETWORK_ERROR";
    console.error("[API] Request failed:", url, err);
    throw err;
  }

  // 204 No Content — no body to parse
  if (res.status === 204) {
    console.log("[API] Response received:", null);
    console.log("[API] Records count:", 0);
    return null;
  }

  let json;
  try {
    json = await res.json();
  } catch {
    const err = new Error(`Unexpected response from server (status ${res.status})`);
    err.code = "PARSE_ERROR";
    err.status = res.status;
    throw err;
  }

  if (!res.ok) {
    const err = new Error(json.message || `Request failed with status ${res.status}`);
    err.code = json.error || "UNKNOWN";
    err.details = json.details || null;
    err.status = res.status;
    console.error("[API] Error response received:", json);
    console.log("[API] Records count:", getRecordCount(json));
    throw err;
  }

  console.log("[API] Response received:", json);
  console.log("[API] Records count:", getRecordCount(json));
  return json;
}

export const api = {
  get:    (path)        => request("GET",    path),
  post:   (path, body)  => request("POST",   path, body),
  put:    (path, body)  => request("PUT",    path, body),
  patch:  (path, body)  => request("PATCH",  path, body),
  delete: (path)        => request("DELETE", path),
};
