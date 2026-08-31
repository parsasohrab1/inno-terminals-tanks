import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { Stat } from "../components/ui";

export default function Reports() {
  const { t } = useTranslation();
  const kpi = useQuery({ queryKey: ["kpi30"], queryFn: () => api("/reports/kpi?days=30") });
  const comp = useQuery({ queryKey: ["compliance"], queryFn: () => api("/reports/compliance") });

  return (
    <div className="space-y-4">
      {kpi.data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label="alarms 30d" value={kpi.data.safety.alarms_total} />
            <Stat label="mean response" value={`${kpi.data.safety.mean_response_seconds ?? "—"} s`} />
            <Stat label="leak alerts" value={kpi.data.leak_prediction.alerts_fired}
              sub={`TP ${kpi.data.leak_prediction.true_positives} / FP ${kpi.data.leak_prediction.false_positives}`} />
            <Stat label="ops volume" value={`${kpi.data.operations.total_volume_m3} m³`}
              sub={`${kpi.data.operations.total_energy_kwh} kWh`} />
          </div>
          <div className="card p-4">
            <div className="font-semibold mb-2">{t("kpi")} — raw</div>
            <pre className="text-xs overflow-x-auto">{JSON.stringify(kpi.data, null, 2)}</pre>
          </div>
        </>
      )}
      {comp.data && (
        <div className="card p-4">
          <div className="font-semibold mb-2">{t("compliance")} (API RP 2350 / IEC 61511)</div>
          <pre className="text-xs overflow-x-auto">{JSON.stringify(comp.data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
