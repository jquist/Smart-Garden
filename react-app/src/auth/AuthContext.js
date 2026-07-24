import React, { createContext, useContext, useEffect, useState } from "react";
import { API } from "../constants";

const AuthContext = createContext(null);

function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split(";") : [];

  for (const cookie of cookies) {
    const [rawKey, ...rawValue] = cookie.trim().split("=");
    if (rawKey === name) return decodeURIComponent(rawValue.join("="));
  }

  return "";
}

export async function ensureCsrfCookie() {
  await fetch(`${API}auth/csrf/`, {
    credentials: "include",
  });
}

export async function apiFetch(path, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  const headers = {
    ...(options.headers || {}),
  };

  if (!headers["Content-Type"] && options.body) {
    headers["Content-Type"] = "application/json";
  }

  if (!["GET", "HEAD", "OPTIONS", "TRACE"].includes(method)) {
    await ensureCsrfCookie();
    headers["X-CSRFToken"] = getCookie("csrftoken");
  }

  const response = await fetch(`${API}${path}`, {
    ...options,
    method,
    headers,
    credentials: "include",
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.error || data?.detail || "Something went wrong.");
  }

  return data;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  async function refreshUser() {
    const data = await apiFetch("auth/me/");
    setUser(data?.is_authenticated ? data.user : null);
    return data;
  }

  async function login({ username, password }) {
    const data = await apiFetch("auth/login/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setUser(data.user);
    return data;
  }

  async function signup({ username, email, password }) {
    const data = await apiFetch("auth/signup/", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });
    setUser(data.user);
    return data;
  }

  async function updateProfile({ username, email }) {
    const data = await apiFetch("auth/profile/", {
      method: "PUT",
      body: JSON.stringify({ username, email }),
    });
    setUser(data.user);
    return data;
  }

  async function changePassword({ currentPassword, newPassword }) {
    return apiFetch("auth/password/", {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  }

  async function logout() {
    await apiFetch("auth/logout/", {
      method: "POST",
      body: JSON.stringify({}),
    });
    setUser(null);
  }

  useEffect(() => {
    apiFetch("auth/me/")
      .catch(() => setUser(null))
      .then((data) => {
        if (data) setUser(data?.is_authenticated ? data.user : null);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    login,
    signup,
    updateProfile,
    changePassword,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}
