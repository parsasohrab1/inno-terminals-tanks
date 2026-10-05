import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, useAuth } from "../api";

export default function Admin() {
  const { t } = useTranslation();
  const role = useAuth((s) => s.role);
  const vault = useQuery({
    queryKey: ["vault"],
    queryFn: () => api("/admin/ip-vault"),
    retry: false,
  });
  const audit = useQuery({
    queryKey: ["audit"],
    queryFn: () => api("/admin/audit?limit=100"),
    retry: false,
  });

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <div className="font-semibold mb-2">{t("ip_vault")}</div>
        {vault.isError && <div className="text-sm text-muted">Restricted access (senior manager only).</div>}
        {vault.data && (
          <>
            <div className="text-sm mb-2">
              Status: <b className={vault.data.vault_unlocked ? "text-brand" : ""}>
                {vault.data.vault_unlocked ? t("vault_unlocked") : t("vault_locked")}
              </b>
            </div>
            <ul className="text-sm space-y-1">
              {Object.entries(vault.data.active_features).map(([k, v]: any) => (
                <li key={k}>{v ? "🟢" : "⚪"} {k}</li>
              ))}
            </ul>
            <div className="text-xs text-muted mt-2">{vault.data.note}</div>
            <div className="text-xs text-muted mt-1">
              blobs: {vault.data.encrypted_modules.join(", ")}
            </div>
          </>
        )}
      </div>

      <div className="card p-4">
        <div className="font-semibold mb-2">{t("audit_log")}</div>
        {audit.isError && <div className="text-sm text-muted">Restricted access.</div>}
        {audit.data && (
          <>
            <div className="text-xs mb-2">
              chain intact: {audit.data.chain_intact ? "✅" : "❌ tamper detected"}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="text-muted border-b border-border">
                  <tr><th className="text-start p-1">ts</th><th className="text-start p-1">user</th>
                    <th className="text-start p-1">action</th><th className="text-start p-1">target</th></tr>
                </thead>
                <tbody>
                  {audit.data.entries.map((e: any) => (
                    <tr key={e.id} className="border-b border-border/40">
                      <td className="p-1">{String(e.ts).slice(0, 19).replace("T", " ")}</td>
                      <td className="p-1">{e.user}</td>
                      <td className="p-1">{e.action}</td>
                      <td className="p-1">{e.target}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      <div className="text-xs text-muted">signed in as {role}</div>
    </div>
  );
}
