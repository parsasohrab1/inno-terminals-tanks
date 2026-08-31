import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, useAuth } from "../api";
import { Dot, TrendChart } from "../components/ui";

const PARAMS = ["level", "pressure", "flammable_gas_ppm", "vibration_mm_s", "temperature", "h2s_ppm"];

export default function TankDetail() {
  const { id } = useParams();
  const { t } = useTranslation();
  const role = useAuth((s) => s.role);
  const [param, setParam] = useState("flammable_gas_ppm");
  const [sim, setSim] = useState<any>(null);

  const tank = useQuery({ queryKey: ["tank", id], queryFn: () => api(`/tanks/${id}`) });
  const trend = useQuery({
    queryKey: ["trend", id, param],
    queryFn: () => api(`/readings/${id}/trend/${param}?hours=6`),
  });
  const pred = useQuery({
    queryKey: ["pred", id],
    queryFn: () => api(`/predictions/${id}?recompute=true`),
  });

  const canSim = role === "safety" || role === "opsmanager" || role === "admin";

  async function simulate() {
    const r = await api(`/twin/${id}/simulate`, {
      method: "POST",
      body: JSON.stringify({ minutes: 90, leak: true }),
    });
    setSim(r);
  }

  return (
    <div className="space-y-4">
      {tank.data && (
        <div className="card p-4 flex items-center gap-3 flex-wrap">
          <Dot status={tank.data.status} />
          <span className="font-bold text-lg">{tank.data.code}</span>
          <span className="text-sm text-muted">
            {tank.data.product} · {tank.data.capacity_m3} m³ · Zone {tank.data.zone}
          </span>
          {tank.data.latest && (
            <span className="text-sm ms-auto">
              {t("level")}: {tank.data.latest.level}% · {t("pressure")}: {tank.data.latest.pressure} bar
            </span>
          )}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card p-4 lg:col-span-2">
          <div className="flex gap-1 flex-wrap mb-2">
            {PARAMS.map((p) => (
              <button key={p} className={`btn ${param === p ? "btn-brand" : "btn-ghost"}`}
                onClick={() => setParam(p)}>{p}</button>
            ))}
          </div>
          {trend.data?.points?.length ? (
            <TrendChart data={trend.data.points} />
          ) : (
            <div className="text-sm text-muted">{t("no_data")}</div>
          )}
        </div>

        <div className="card p-4">
          <div className="font-semibold mb-2">{t("predictions")}</div>
          {pred.data && (
            <>
              <div className="text-3xl font-bold"
                style={{ color: pred.data.probability > 0.6 ? "#ef4444" : "inherit" }}>
                {(pred.data.probability * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-muted">
                {t("horizon")}: {pred.data.horizon_minutes}min · model: {pred.data.model} ·
                CI [{pred.data.confidence_interval.map((x: number) => x.toFixed(2)).join(", ")}]
              </div>
              <div className="mt-3 text-sm font-medium">{t("explanation")}</div>
              <ul className="text-xs space-y-1 mt-1">
                {Object.entries(pred.data.explanation || {}).map(([k, v]: any) => (
                  <li key={k} className="flex justify-between gap-2">
                    <span className="truncate">{k}</span>
                    <span className="tabular-nums">{(v as number).toFixed(3)}</span>
                  </li>
                ))}
              </ul>
              {pred.data.propagation && Object.keys(pred.data.propagation).length > 0 && (
                <>
                  <div className="mt-3 text-sm font-medium">{t("propagation")}</div>
                  <ul className="text-xs space-y-1 mt-1">
                    {Object.entries(pred.data.propagation).map(([k, v]: any) => (
                      <li key={k} className="flex justify-between">
                        <span>tank #{k}</span>
                        <span>{((v as number) * 100).toFixed(0)}%</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </>
          )}
          {canSim && (
            <button className="btn btn-ghost w-full mt-4" onClick={simulate}>
              {t("simulate_leak")}
            </button>
          )}
        </div>
      </div>

      {sim && (
        <div className="card p-4">
          <div className="font-semibold mb-2">
            {t("simulate_leak")} — {sim.engine} · onset @ {sim.leak_onset_minute}min
          </div>
          <TrendChart
            data={sim.trace.map((r: any) => ({ ts: String(r.minute), value: r.flammable_gas_ppm }))}
            color="#f97316"
          />
        </div>
      )}
    </div>
  );
}
