import { ReactNode, useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, connectWs, useAuth } from "../api";
import { setLang } from "../i18n";

const nav = [
  ["/", "dashboard"],
  ["/alarms", "alarms"],
  ["/predictions", "predictions"],
  ["/optimization", "optimization"],
  ["/reports", "reports"],
  ["/admin", "admin"],
] as const;

export default function Layout({ children }: { children: ReactNode }) {
  const { t, i18n } = useTranslation();
  const { username, role, logout } = useAuth();
  const nvg = useNavigate();
  const [dark, setDark] = useState(localStorage.getItem("theme") === "dark");
  const [toast, setToast] = useState<string | null>(null);
  const [vault, setVault] = useState<boolean | null>(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    api("/admin/health").then((r: any) => setVault(r.ip_vault_unlocked)).catch(() => {});
    const ws = connectWs((topic, data) => {
      if (topic === "alarm" && (data.severity === "critical" || data.severity === "high")) {
        setToast(`${data.title}`);
        setTimeout(() => setToast(null), 6000);
      }
    });
    return () => ws.close();
  }, []);

  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-border bg-surface">
        <div className="max-w-[1400px] mx-auto px-4 h-14 flex items-center gap-4">
          <div className="font-bold text-brand">INNO</div>
          <div className="text-sm text-muted hidden md:block">{t("app")}</div>
          <nav className="flex gap-1 ms-auto flex-wrap">
            {nav.map(([to, key]) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `btn ${isActive ? "btn-brand" : "btn-ghost"}`
                }
              >
                {t(key)}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <div className="max-w-[1400px] w-full mx-auto px-4 py-2 flex items-center gap-3 text-xs text-muted">
        <span>{username} · {role}</span>
        <span className={`badge ${vault ? "bg-brand/15 text-brand" : "bg-border/40"}`}>
          {t("ip_vault")}: {vault === null ? "…" : vault ? t("vault_unlocked") : t("vault_locked")}
        </span>
        <button className="btn btn-ghost ms-auto" onClick={() => setDark(!dark)}>
          {t("dark_mode")}: {dark ? "on" : "off"}
        </button>
        <button
          className="btn btn-ghost"
          onClick={() => setLang(i18n.language === "fa" ? "en" : "fa")}
        >
          {i18n.language === "fa" ? "EN" : "فا"}
        </button>
        <button className="btn btn-ghost" onClick={() => { logout(); nvg("/"); }}>
          {t("logout")}
        </button>
      </div>

      <main className="max-w-[1400px] w-full mx-auto px-4 py-4 flex-1">{children}</main>

      {toast && (
        <div className="fixed bottom-4 end-4 card px-4 py-3 border-red-500/50 bg-red-500/10 text-sm max-w-sm">
          🚨 {toast}
        </div>
      )}
    </div>
  );
}
