import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { fetchMetrics, DashboardMetrics } from "../api/client";

const STAGE_COLORS: Record<string, string> = {
  NEW: "#94a3b8",
  WARM: "#f59e0b",
  HOT: "#ef4444",
  DISQUALIFIED: "#e2e8f0",
};

export default function Dashboard() {
  const [days, setDays] = useState(7);
  const { data, isLoading } = useQuery<DashboardMetrics>({
    queryKey: ["metrics", days],
    queryFn: () => fetchMetrics(days),
    refetchInterval: 30000,
  });

  if (isLoading || !data) return <div className="p-8 text-gray-500">Loading...</div>;

  const stageData = Object.entries(data.by_stage).map(([stage, count]) => ({ stage, count }));

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="border rounded px-3 py-1.5 text-sm"
        >
          {[7, 14, 30, 90].map((d) => (
            <option key={d} value={d}>Last {d} days</option>
          ))}
        </select>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Total Leads" value={data.total_leads} />
        <KpiCard label="HOT Rate" value={`${data.hot_rate_pct}%`} accent="red" />
        <KpiCard label="Handoffs" value={data.total_handoffs} />
        <KpiCard label="Avg Score" value={data.avg_score} />
      </div>

      {/* SLA */}
      {data.total_handoffs > 0 && (
        <div className="bg-white rounded-xl border p-4">
          <p className="text-sm font-medium text-gray-600 mb-1">
            SLA (&lt;30 min acceptance)
          </p>
          <div className="w-full bg-gray-100 rounded-full h-3">
            <div
              className="bg-green-500 h-3 rounded-full transition-all"
              style={{ width: `${(data.sla_met / data.total_handoffs) * 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {data.sla_met} / {data.total_handoffs} within SLA
          </p>
        </div>
      )}

      {/* Stage breakdown chart */}
      <div className="bg-white rounded-xl border p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Leads by Stage</h2>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={stageData} barCategoryGap="40%">
            <XAxis dataKey="stage" tick={{ fontSize: 12 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {stageData.map((entry) => (
                <Cell key={entry.stage} fill={STAGE_COLORS[entry.stage] || "#6366f1"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function KpiCard({
  label, value, accent,
}: { label: string; value: string | number; accent?: string }) {
  return (
    <div className="bg-white rounded-xl border p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${accent === "red" ? "text-red-500" : "text-gray-900"}`}>
        {value}
      </p>
    </div>
  );
}
