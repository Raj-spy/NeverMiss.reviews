// frontend/src/lib/api.ts
// Axios instance with auth token injection and error handling

import axios from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Inject JWT token on every request
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      Cookies.remove("access_token");
      window.location.href = "/auth/login";
    }
    return Promise.reject(err);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  signup: (data: { email: string; password: string; full_name?: string }) =>
    api.post("/auth/signup", data),

  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
};

// ─── Business ─────────────────────────────────────────────────────────────────

export const businessApi = {
  list: () => api.get("/business"),
  get: (id: string) => api.get(`/business/${id}`),
  create: (data: { business_name: string; google_maps_url: string; description?: string }) =>
    api.post("/business", data),
  delete: (id: string) => api.delete(`/business/${id}`),
  refresh: (id: string) => api.post(`/business/${id}/refresh`),
};

// ─── Reviews ─────────────────────────────────────────────────────────────────

export const reviewsApi = {
  list: (params?: { business_id?: string; rating?: number; processed?: boolean; limit?: number; offset?: number }) =>
    api.get("/reviews", { params }),
  analytics: (business_id?: string) =>
    api.get("/reviews/analytics", { params: business_id ? { business_id } : {} }),
};

// ─── Replies ─────────────────────────────────────────────────────────────────

export const repliesApi = {
  approve: (reply_id: string, edited_text?: string) =>
    api.post("/reply/approve", { reply_id, edited_text }),
  reject: (reply_id: string) =>
    api.post("/reply/reject", { reply_id }),
  getReplies: (review_id: string) =>
    api.get(`/reply/${review_id}`),
  regenerate: (review_id: string) =>
    api.post(`/reply/${review_id}/regenerate`),
};

export default api;
