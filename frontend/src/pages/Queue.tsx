import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import {
  fetchQueue, acceptHandoff, resolveHandoff,
  HandoffItem,
} from "../api/client";

const AGENT_ID = "agent-001"; // In production, pull from auth context

const STAGE_BADGE: Record<string, string> = {
  NEW: "bg-gray-100 text-gray-700",
  WARM: "bg-amber-100 text-amber-700",
  HOT: "bg-red-100 text-red-700",
  DISQUALIFIED: "bg-slate-100 text-slate-500",
};

const TRIGGER_LABEL: Record<string, string> = {
  HIGH_SCORE: "High Score",
  CUSTOMER_REQUEST: "Customer Request",
  LOOP_ESCALATION: "Loop Escalation",
};

export default function Queue() {
  const qc = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: queue = [], isLoading } = useQuery<HandoffItem[]>({
    queryKey: ["handoff-queue"],
    queryFn: fetchQueue,
    refetchInterval: 15000,
  });

  const acceptMut = useMutation({
    mutationFn: (id: string) => acceptHandoff(id, AGENT_ID),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["handoff-queue"] }),
  });

  const resolveMut = useMutation({
    mutationFn: (id: string) => resolveHandoff(id, AGENT_ID),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["handoff-queue"] });
      setSelectedId(null);
    },
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading queue...</div>;

  const pending = queue.filter((h) => !h.accepted_at);
  const inProgress = queue.filter((h) => h.accepted_at && !h.resolved_at);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">
        Handoff Queue
        {pending.length > 0 && (
          <span className="ml-2 text-sm bg-red-500 text-white rounded-full px-2 py-0.5">
            {pending.length} new
          </span>
        )}
      </h1>

      {queue.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          No pending handoffs. Priya is handling everything.
        </div>
      )}

      {/* Pending */}
      {pending.length > 0 && (
        <Section title="Pending">
          {pending.map((h) => (
            <HandoffCard
              key={h.id}
              item={h}
              onAccept={() => acceptMut.mutate(h.id)}
              onOpen={() => setSelectedId(h.id)}
            />
          ))}
        </Section>
      )}

      {/* In Progress */}
      {inProgress.length > 0 && (
        <Section title="In Progress">
          {inProgress.map((h) => (
            <HandoffCard
              key={h.id}
              item={h}
              onResolve={() => resolveMut.mutate(h.id)}
              onOpen={() => setSelectedId(h.id)}
            />
          ))}
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">{title}</h2>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function HandoffCard({
  item, onAccept, onResolve, onOpen,
}: {
  item: HandoffItem;
  onAccept?: () => void;
  onResolve?: () => void;
  onOpen?: () => void;
}) {
  const { lead } = item;
  return (
    <div className="bg-white rounded-xl border p-4 flex items-start justify-between gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-gray-900">{lead.name || lead.phone}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STAGE_BADGE[lead.stage]}`}>
            {lead.stage}
          </span>
          <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">
            Score: {lead.score}
          </span>
          <span className="text-xs text-gray-400">
            {TRIGGER_LABEL[item.trigger_reason] || item.trigger_reason}
          </span>
        </div>
        <p className="text-sm text-gray-600 mt-1 truncate">
          {[lead.project_type, lead.project_location, lead.material_needed, lead.volume_mt]
            .filter(Boolean)
            .join(" · ")}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          {formatDistanceToNow(new Date(item.triggered_at), { addSuffix: true })}
        </p>
      </div>
      <div className="flex flex-col gap-2 shrink-0">
        <button
          onClick={onOpen}
          className="text-xs border rounded px-3 py-1 text-gray-600 hover:bg-gray-50"
        >
          View Chat
        </button>
        {onAccept && (
          <button
            onClick={onAccept}
            className="text-xs bg-indigo-600 text-white rounded px-3 py-1 hover:bg-indigo-700"
          >
            Accept
          </button>
        )}
        {onResolve && (
          <button
            onClick={onResolve}
            className="text-xs bg-green-600 text-white rounded px-3 py-1 hover:bg-green-700"
          >
            Resolve
          </button>
        )}
      </div>
    </div>
  );
}
