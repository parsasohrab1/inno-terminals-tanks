import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";

export default function Predictions() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const preds = useQuery({ queryKey: ["preds"], queryFn: () => api("/predictions") });
  const list: any[] = preds.data || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <button className="btn btn-brand" onClick={async () => {
          await api("/predictions/run", { method: "POST" });
          qc.invalidateQueries({ queryKey: ["preds"] });
        }}>{t("run_prediction")}</button>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {list.map((p) => (
          <Link key={p.tank_id} to={`/tanks/${p.tank_id}`} className="card p-4 hover:border-brand">
            <div className="flex justify-between items-center">
              <span className="font-semibold">{p.tank_code}</span>
              <span className="text-2xl font-bold"
                style={{ color: p.probability > 0.6 ? "#ef4444" : p.probability > 0.3 ? "#eab308" : "inherit" }}>
                {(p.probability * 100).toFixed(0)}%
              </span>
            </div>
            <div className="text-xs text-muted mt-1">
              {t("horizon")}: {p.horizon_minutes}min · {p.model}
              {p.will_leak && <span className="text-red-500 font-semibold"> · ALERT</span>}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
