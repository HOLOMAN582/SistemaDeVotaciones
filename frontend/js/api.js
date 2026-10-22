const API_BASE_URL = "http://127.0.0.1:8000";
const TOKEN_STORAGE_KEY = "votaciones_access_token";

async function apiRequest(path, options = {}) {
  const token = sessionStorage.getItem(TOKEN_STORAGE_KEY);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `Error HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Mantiene el mensaje HTTP cuando la respuesta no es JSON.
    }
    throw new Error(detail);
  }

  if (response.status === 204) return null;
  return response.json();
}

async function login(username, password) {
  const role = document.querySelector("#login-role").value;
  const result = await apiRequest(role === "admin" ? "/auth/login" : "/auth/voter-login", {
    method: "POST",
    body: JSON.stringify(role === "admin" ? { username, password } : { email: username, password }),
  });
  sessionStorage.setItem(TOKEN_STORAGE_KEY, result.access_token);
  sessionStorage.setItem("votaciones_role", result.role);
  if (result.voter_id) sessionStorage.setItem("votaciones_voter_id", String(result.voter_id));
}

function logout() {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  sessionStorage.removeItem("votaciones_role");
  sessionStorage.removeItem("votaciones_voter_id");
}

function isAuthenticated() {
  return Boolean(sessionStorage.getItem(TOKEN_STORAGE_KEY));
}

function currentRole() {
  return sessionStorage.getItem("votaciones_role");
}
