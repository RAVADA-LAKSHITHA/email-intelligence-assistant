export const API_URL = import.meta.env.VITE_API_URL;

export const LOGIN_URL = `${API_URL}/api/auth/google/login`;

async function request(method, path, params = {}) {
  const url = new URL(`${API_URL}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });

  // credentials: "include" makes the browser send the login cookie.
  const response = await fetch(url, { method, credentials: "include" });

  if (response.status === 401) {
    // Tell the app the session is gone, so it can show the login screen.
    window.dispatchEvent(new Event("session-expired"));
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

export const apiGet = (path, params) => request("GET", path, params);
export const apiPost = (path, params) => request("POST", path, params);