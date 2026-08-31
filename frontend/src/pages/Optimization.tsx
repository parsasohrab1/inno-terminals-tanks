import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { Stat } from "../components/ui";

export default function Optimization() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const ops = useQuery({ queryKey: ["ops"], queryFn: () => api("/optimization/operations") });
  const [plan, setPlan] = useState<any>(null);
  const [wi, setWi] = useState<any>(null);

  async function build() {
    const p = await api("/optimization/plan", { method: "POST" });
    setPlan(p);
    qc.invalidateQueries({ queryKey: ["ops"] });
  }
  async function whatIf() {
    const p = await api("/optimization/what-if", {
      method: "POST",
      body: JSON.stringify({ disabled_pumps: ["P-1"], pump_count: 3 }),
    });
    setWi(p);
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2 flex-wrap">
        <button className="btn btn-brand" onClick={build}>{t("build_plan")}</button>
        <button className="btn btn-ghost" onClick={whatIf}>{t("what_if")}: pump P-1 down</button>
      </div>

      {plan && (
        <div className="card p-4 space-y-3">
          <div className="flex gap-2 items-center flex-wrap text-sm">
            <span className="badge bg-brand/15 text-brand">{plan.algorithm}</span>
            {plan.risk_aware && <span className="badge bg-brand/15 text-brand">{t("risk_aware")}</span>}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label={t("makespan")} value={`${Math.round(plan.makespan_minutes)} min`} />
            <Stat label={t("energy")} value={`${plan.total_energy_kwh} kWh`} />
            <Stat label={t("max_risk")} value={`${(plan.max_leak_risk * 100).toFixed(1)}%`} />
            <Stat label="deferrals" value={plan.high_risk_deferrals} />
          </div>
          <table className="w-full text-sm">
            <thead className="text-xs text-muted border-b border-border">
              <tr><th className="text-start p-2">ref</th><th className="text-start p-2">tank</th>
                <th className="text-start p-2">pump</th><th className="text-start p-2">start</th>
                <th className="text-start p-2">risk</th><th className="text-start p-2">kWh</th></tr>
            </thead>
            <tbody>
              {plan.schedule.map((s: any, i: number) => (
                <tr key={i} className="border-b border-border/40">
                  <td className="p-2">{s.ref || "—"}</td>
                  <td className="p-2">#{s.tank_id} ({s.kind})</td>
                  <td className="p-2">{s.pump_id}</td>
                  <td className="p-2">{String(s.planned_start).slice(5, 16).replace("T", " ")}</td>
                  <td className="p-2" style={{ color: s.predicted_leak_risk > 0.5 ? "#ef4444" : "inherit" }}>
                    {(s.predicted_leak_risk * 100).toFixed(1)}%</td>
                  <td className="p-2">{s.energy_kwh}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {wi && (
        <div className="card p-4 text-sm">
          <div className="font-semibold mb-1">{t("what_if")}</div>
          disabled: {wi.disabled_pumps.join(", ")} → effective pumps: {wi.effective_pumps},
          makespan {Math.round(wi.makespan_minutes)} min
        </div>
      )}

      <div className="card p-4">
        <div className="font-semibold mb-2">{t("optimization")} — operations</div>
        <table className="w-full text-sm">
          <thead className="text-xs text-muted border-b border-border">
            <tr><th className="text-start p-2">ref</th><th className="text-start p-2">tank</th>
              <th className="text-start p-2">kind</th><th className="text-start p-2">vol</th>
              <th className="text-start p-2">prio</th><th className="text-start p-2">state</th></tr>
          </thead>
          <tbody>
            {(ops.data || []).map((o: any) => (
              <tr key={o.id} className="border-b border-border/40">
                <td className="p-2">{o.ref || o.id}</td>
                <td className="p-2">#{o.tank_id}</td>
                <td className="p-2">{o.kind}</td>
                <td className="p-2">{o.volume_m3} m³</td>
                <td className="p-2">{o.priority}</td>
                <td className="p-2">{o.state}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
