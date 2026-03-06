// frontend/src/lib/auth.ts
// Auth state management using cookies and local state helpers

import Cookies from "js-cookie";

export interface AuthUser {
  user_id: string;
  email: string;
  access_token: string;
}

export function saveAuth(data: AuthUser) {
  Cookies.set("access_token", data.access_token, { expires: 1 }); // 1 day
  if (typeof window !== "undefined") {
    localStorage.setItem("user", JSON.stringify({ user_id: data.user_id, email: data.email }));
  }
}

export function getStoredUser(): { user_id: string; email: string } | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearAuth() {
  Cookies.remove("access_token");
  if (typeof window !== "undefined") {
    localStorage.removeItem("user");
  }
}

export function isAuthenticated(): boolean {
  return !!Cookies.get("access_token");
}
