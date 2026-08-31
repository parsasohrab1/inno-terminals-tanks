import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export const STATUS_COLOR: Record<string, string> = {
  green: "#16a34a",
  yellow: "#eab308",
  red: "#ef4444",
  offline: "#64748b",
};

export const SEV_COLOR: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#3b82f6",
};

export function Dot({ status }: { status: string }) {
  return (
    <span
      className="inline-block w-2.5 h-2.5 rounded-full"
      style={{ background: STATUS_COLOR[status] || "#64748b" }}
    />
  );
}

export function Stat({ label, value, sub }: { label: string; value: any; sub?: string }) {
  return (
    <div className="card p-3">
      <div className="text-xs text-muted">{label}</div>
      <div className="text-xl font-semibold mt-1">{value}</div>
      {sub && <div className="text-xs text-muted mt-0.5">{sub}</div>}
    </div>
  );
}

export function TrendChart({
  data,
  dataKey = "value",
  color = "#2dd4bf",
  height = 220,
}: {
  data: any[];
  dataKey?: string;
  color?: string;
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border))" />
        <XAxis dataKey="ts" tick={{ fontSize: 10 }} tickFormatter={(v) => String(v).slice(11, 16)}
          minTickGap={40} stroke="rgb(var(--muted))" />
        <YAxis tick={{ fontSize: 10 }} stroke="rgb(var(--muted))" width={48} domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{ background: "rgb(var(--surface))", border: "1px solid rgb(var(--border))",
            borderRadius: 8, fontSize: 12 }}
          labelFormatter={(v) => String(v).replace("T", " ").slice(0, 19)}
        />
        <Line type="monotone" dataKey={dataKey} stroke={color} dot={false} strokeWidth={2} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
