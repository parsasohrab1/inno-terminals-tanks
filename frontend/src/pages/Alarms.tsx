import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { SEV_COLOR } from "../components/ui";

export default function Alarms() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const alarms = useQuery({ queryKey: ["alarms"], queryFn: () => api("/alarms?limit=300") });
  const rate = useQuery({ queryKey: ["alarm-rate"], queryFn: () => api("/alarms/rate") });

  async function act(id: number, action: "ack" | "clear") {
    try {
      await api(`/alarms/${id}/${action}`, { method: "POST", body: JSON.stringify({ note: "" }) });
    } catch (e: any) {
      alert(String(e.message || e).slice(0, 300));
    }
    qc.invalidateQueries({ queryKey: ["alarms"] });
  }

  const list: any[] = alarms.data || [];

  return (
    <div className="space-y-4">
      {rate.data && (
        <div className={`card p-3 text-sm ${rate.data.within_target ? "" : "border-yellow-500/50"}`}>
          ISA-18.2: {rate.data.per_operator_hour} هشدار/اپراتور/ساعت (هدف ≤ {rate.data.isa_18_2_target})
          {rate.data.within_target ? " ✅" : " ⚠️ بار هشدار بالا"}
        </div>
      )}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-muted text-xs border-b border-border">
            <tr>
              <th className="text-start p-2">#</th>
              <th className="text-start p-2">{t("severity")}</th>
              <th className="text-start p-2">tank</th>
              <th className="text-start p-2">title</th>
              <th className="text-start p-2">{t("state")}</th>
              <th className="text-start p-2">ack</th>
              <th className="p-2"></th>
            </tr>
          </thead>
          <tbody>
            {list.map((a) => (
              <tr key={a.id} className="border-b border-border/50">
                <td className="p-2 tabular-nums">{a.id}</td>
                <td className="p-2">
                  <span className="badge" style={{ background: SEV_COLOR[a.severity] + "22", color: SEV_COLOR[a.severity] }}>
                    {t(a.severity)}
                  </span>
                </td>
                <td className="p-2">{a.tank_id ?? "—"}</td>
                <td className="p-2">
                  {a.title}
                  {a.suppressed_reason && <div className="text-xs text-muted">{a.suppressed_reason}</div>}
                </td>
                <td className="p-2">{a.state}</td>
                <td className="p-2 tabular-nums">
                  {a.ack_count}{a.requires_two_person ? "/2" : ""}
                </td>
                <td className="p-2 flex gap-1 justify-end">
                  {a.state !== "cleared" && (
                    <>
                      <button className="btn btn-ghost" onClick={() => act(a.id, "ack")}>{t("acknowledge")}</button>
                      <button className="btn btn-ghost" onClick={() => act(a.id, "clear")}>{t("clear")}</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {list.length === 0 && (
              <tr><td colSpan={7} className="p-4 text-center text-muted">{t("no_data")}</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
