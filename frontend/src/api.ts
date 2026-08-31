import { create } from "zustand";
import { persist } from "zustand/middleware";

const BASE = "/api/v1";

type AuthState = {
  token: string | null;
  role: string | null;
  username: string | null;
  setAuth: (t: string, role: string, username: string) => void;
  logout: () => void;
};

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      role: null,
      username: null,
      setAuth: (token, role, username) => set({ token, role, username }),
      logout: () => set({ token: null, role: null, username: null }),
    }),
    { name: "inno-auth" },
  ),
);

export async function api<T = any>(path: string, opts: RequestInit = {}): Promise<T> {
  const { token } = useAuth.getState();
  const res = await fetch(BASE + path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
  });
  if (res.status === 401) {
    useAuth.getState().logout();
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || res.statusText);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("json") ? res.json() : (res.text() as any);
}

export async function login(username: string, password: string, totp?: string) {
  const data = await api<{ access_token: string; role: string }>("/auth/login-json", {
    method: "POST",
    body: JSON.stringify({ username, password, totp: totp || null }),
  });
  useAuth.getState().setAuth(data.access_token, data.role, username);
  return data;
}

export function connectWs(onMessage: (topic: string, data: any) => void): WebSocket {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/api/v1/ws`);
  ws.onmessage = (e) => {
    try {
      const { topic, data } = JSON.parse(e.data);
      onMessage(topic, data);
    } catch {
      /* ignore */
    }
  };
  return ws;
}
