import React from "react";

const COLORS: Record<string, string> = {
  NEW: "bg-gray-100 text-gray-600",
  WARM: "bg-amber-100 text-amber-700",
  HOT: "bg-red-100 text-red-600 font-semibold",
  DISQUALIFIED: "bg-slate-100 text-slate-400",
};

export default function QualificationBadge({ stage, score }: { stage: string; score: number }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${COLORS[stage] || "bg-gray-100"}`}>
      {stage}
      <span className="opacity-70">({score})</span>
    </span>
  );
}
