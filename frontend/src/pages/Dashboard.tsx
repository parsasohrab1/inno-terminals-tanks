import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { Dot, STATUS_COLOR, Stat } from "../components/ui";

export default function Dashboard() {
  const { t } = useTranslation();
  const tanks = useQuery({ queryKey: ["tanks"], queryFn: () => api("/tanks") });
  const map = useQuery({ queryKey: ["map"], queryFn: () => api("/tanks/map") });
  const kpi = useQuery({ queryKey: ["kpi"], queryFn: () => api("/reports/kpi?days=7") });

  const list: any[] = tanks.data || [];
  const counts = list.reduce((a, t) => ((a[t.status] = (a[t.status] || 0) + 1), a), {} as any);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label={t("green")} value={counts.green || 0} />
        <Stat label={t("yellow")} value={counts.yellow || 0} />
        <Stat label={t("red")} value={counts.red || 0} />
        <Stat label={t("offline")} value={counts.offline || 0} />
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-4 lg:col-span-2">
          <div className="font-semibold mb-2">{t("terminal_map")}</div>
          <TerminalMap map={map.data} tanks={list} />
        </div>
        <div className="card p-4">
          <div className="font-semibold mb-2">{t("kpi")} (7d)</div>
          {kpi.data && (
            <ul className="text-sm space-y-1">
              <li>Alarms: {kpi.data.safety.alarms_total} (suppressed: {kpi.data.safety.alarms_suppressed})</li>
              <li>Mean response time: {kpi.data.safety.mean_response_seconds ?? "—"}s</li>
              <li>ISA-18.2: {kpi.data.safety.isa_18_2.per_operator_hour}/hour
                {kpi.data.safety.isa_18_2.within_target ? " ✅" : " ⚠️"}</li>
              <li>Leak prediction: {kpi.data.leak_prediction.alerts_fired} alerts /
                {kpi.data.leak_prediction.confirmed_leaks} confirmed</li>
              <li>Completed operations: {kpi.data.operations.completed}</li>
            </ul>
          )}
        </div>
      </div>

      <div className="card p-4">
        <div className="font-semibold mb-3">{t("fleet_status")}</div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {list.map((tk) => (
            <Link key={tk.id} to={`/tanks/${tk.id}`}
              className="card p-3 hover:border-brand transition-colors block">
              <div className="flex items-center justify-between">
                <span className="font-semibold">{tk.code}</span>
                <Dot status={tk.status} />
              </div>
              <div className="text-xs text-muted">{tk.product} · {tk.capacity_m3} m³ · Zone {tk.zone}</div>
              {tk.latest ? (
                <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-xs mt-2">
                  <span>{t("level")}: {tk.latest.level}%</span>
                  <span>{t("pressure")}: {tk.latest.pressure} bar</span>
                  <span>{t("flammable_gas")}: {tk.latest.flammable_gas_ppm}</span>
                  <span>{t("vibration")}: {tk.latest.vibration_mm_s}</span>
                </div>
              ) : (
                <div className="text-xs text-muted mt-2">{t("no_data")}</div>
              )}
              {tk.leak_probability != null && (
                <div className="mt-2 text-xs">
                  {t("leak_probability")}:{" "}
                  <b style={{ color: tk.leak_probability > 0.6 ? "#ef4444" : "inherit" }}>
                    {(tk.leak_probability * 100).toFixed(0)}%
                  </b>
                </div>
              )}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

function TerminalMap({ map, tanks }: { map: any; tanks: any[] }) {
  if (!map) return null;
  const statusById: Record<number, string> = {};
  tanks.forEach((t) => (statusById[t.id] = t.status));
  return (
    <svg viewBox="0 0 100 80" className="w-full h-[340px] rounded-lg" style={{ background: "rgb(var(--bg))" }}>
      {map.pipelines.map((p: any) => {
        const a = map.tanks.find((x: any) => x.id === p.from);
        const b = map.tanks.find((x: any) => x.id === p.to);
        if (!a || !b) return null;
        return <line key={p.id} x1={a.x * 100} y1={a.y * 80} x2={b.x * 100} y2={b.y * 80}
          stroke="rgb(var(--border))" strokeWidth={0.6} />;
      })}
      {map.tanks.map((tk: any) => (
        <g key={tk.id}>
          <circle cx={tk.x * 100} cy={tk.y * 80} r={2.6}
            fill={STATUS_COLOR[statusById[tk.id] || tk.status] || "#64748b"} />
          <text x={tk.x * 100} y={tk.y * 80 - 3.4} textAnchor="middle" fontSize={2.4}
            fill="rgb(var(--muted))">{tk.code}</text>
        </g>
      ))}
    </svg>
  );
}
