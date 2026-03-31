import axios from "axios";

// Lazy import to avoid circular dependency — store may not be initialized at module load
let _getAuthState: (() => { token: string | null; logout: () => void }) | null =
  null;

export function bindAuthStore(
  getState: () => { token: string | null; logout: () => void },
) {
  _getAuthState = getState;
}

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// ── Request interceptor: attach Bearer token ─────────────────────────────────
api.interceptors.request.use((config) => {
  const state = _getAuthState?.();
  if (state?.token) {
    config.headers.Authorization = `Bearer ${state.token}`;
  }
  return config;
});

// ── Response interceptor: handle 401 → logout + redirect ─────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const state = _getAuthState?.();
      state?.logout();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default api;
