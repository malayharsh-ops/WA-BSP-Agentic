import React, { useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchCampaigns, createCampaign, sendCampaign, uploadContacts,
  Campaign,
} from "../api/client";

const STATUS_BADGE: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-600",
  SCHEDULED: "bg-blue-100 text-blue-700",
  RUNNING: "bg-amber-100 text-amber-700",
  COMPLETED: "bg-green-100 text-green-700",
  FAILED: "bg-red-100 text-red-700",
};

export default function Campaigns() {
  const qc = useQueryClient();
  const [creating, setCreating] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadTarget, setUploadTarget] = useState<string | null>(null);

  const { data: campaigns = [], isLoading } = useQuery<Campaign[]>({
    queryKey: ["campaigns"],
    queryFn: fetchCampaigns,
    refetchInterval: 30000,
  });

  const [form, setForm] = useState({ name: "", template_name: "", language: "hi" });

  const createMut = useMutation({
    mutationFn: () => createCampaign(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      setCreating(false);
      setForm({ name: "", template_name: "", language: "hi" });
    },
  });

  const sendMut = useMutation({
    mutationFn: (id: string) => sendCampaign(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campaigns"] }),
  });

  const uploadMut = useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) => uploadContacts(id, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      setUploadTarget(null);
    },
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
        <button
          onClick={() => setCreating(true)}
          className="bg-indigo-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-indigo-700"
        >
          + New Campaign
        </button>
      </div>

      {/* Create form */}
      {creating && (
        <div className="bg-white border rounded-xl p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">New Campaign</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              placeholder="Campaign name"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="border rounded px-3 py-2 text-sm"
            />
            <input
              placeholder="Template name (Meta approved)"
              value={form.template_name}
              onChange={(e) => setForm((f) => ({ ...f, template_name: e.target.value }))}
              className="border rounded px-3 py-2 text-sm"
            />
            <select
              value={form.language}
              onChange={(e) => setForm((f) => ({ ...f, language: e.target.value }))}
              className="border rounded px-3 py-2 text-sm"
            >
              {[["hi", "Hindi"], ["en", "English"], ["mr", "Marathi"],
                ["gu", "Gujarati"], ["te", "Telugu"], ["kn", "Kannada"], ["ta", "Tamil"]]
                .map(([code, label]) => <option key={code} value={code}>{label}</option>)}
            </select>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => createMut.mutate()}
              disabled={!form.name || !form.template_name}
              className="bg-indigo-600 text-white rounded px-4 py-2 text-sm disabled:opacity-50"
            >
              Create
            </button>
            <button onClick={() => setCreating(false)} className="text-sm text-gray-500 px-4 py-2">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Campaign list */}
      {campaigns.length === 0 && !creating && (
        <div className="text-center py-16 text-gray-400">No campaigns yet.</div>
      )}

      <div className="space-y-3">
        {campaigns.map((c) => (
          <div key={c.id} className="bg-white border rounded-xl p-4 flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900">{c.name}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[c.status]}`}>
                  {c.status}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-0.5">
                Template: <code className="text-xs bg-gray-100 px-1 rounded">{c.template_name}</code>
                {" · "}{c.language.toUpperCase()}
              </p>
            </div>
            <div className="flex gap-2 shrink-0">
              {c.status === "DRAFT" && (
                <>
                  <button
                    onClick={() => { setUploadTarget(c.id); fileInputRef.current?.click(); }}
                    className="text-xs border rounded px-3 py-1.5 text-gray-600 hover:bg-gray-50"
                  >
                    Upload CSV
                  </button>
                  <button
                    onClick={() => sendMut.mutate(c.id)}
                    className="text-xs bg-green-600 text-white rounded px-3 py-1.5 hover:bg-green-700"
                  >
                    Send Now
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Hidden file input for CSV upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file && uploadTarget) {
            uploadMut.mutate({ id: uploadTarget, file });
          }
          if (fileInputRef.current) fileInputRef.current.value = "";
        }}
      />
    </div>
  );
}
