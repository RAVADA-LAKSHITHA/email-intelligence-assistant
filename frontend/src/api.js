export const API_URL = import.meta.env.VITE_API_URL;

export const LOGIN_URL = `${API_URL}/api/auth/google/login`;

async function request(method, path, params = {}) {
  const url = new URL(`${API_URL}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });

  const response = await fetch(url, { method });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

export const apiGet = (path, params) => request("GET", path, params);
export const apiPost = (path, params) => request("POST", path, params);