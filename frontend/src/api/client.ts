import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

export default api;

// ── Types ──────────────────────────────────────────────────────────────────

export interface Lead {
  id: string;
  phone: string;
  name: string | null;
  language: string;
  stage: "NEW" | "WARM" | "HOT" | "DISQUALIFIED";
  score: number;
  project_type: string | null;
  project_location: string | null;
  material_needed: string | null;
  volume_mt: string | null;
  sf_opportunity_id: string | null;
  created_at: string;
}

export interface HandoffItem {
  id: string;
  trigger_reason: string;
  triggered_at: string;
  accepted_at: string | null;
  resolved_at: string | null;
  agent_id: string | null;
  conversation_id: string;
  lead: Lead;
}

export interface Message {
  id: string;
  direction: "IN" | "OUT";
  body: string;
  created_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  template_name: string;
  language: string;
  status: "DRAFT" | "SCHEDULED" | "RUNNING" | "COMPLETED" | "FAILED";
  scheduled_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface DashboardMetrics {
  period_days: number;
  total_leads: number;
  by_stage: Record<string, number>;
  hot_rate_pct: number;
  total_handoffs: number;
  sla_met: number;
  avg_score: number;
}

// ── API calls ─────────────────────────────────────────────────────────────

export const fetchMetrics = (days = 7): Promise<DashboardMetrics> =>
  api.get(`/dashboard/metrics?days=${days}`).then((r) => r.data);

export const fetchQueue = (): Promise<HandoffItem[]> =>
  api.get("/handoff/queue").then((r) => r.data);

export const acceptHandoff = (id: string, agentId: string) =>
  api.post(`/handoff/${id}/accept`, { agent_id: agentId }).then((r) => r.data);

export const resolveHandoff = (id: string, agentId: string, notes = "") =>
  api.post(`/handoff/${id}/resolve`, { agent_id: agentId, notes }).then((r) => r.data);

export const agentSend = (id: string, agentId: string, body: string) =>
  api.post(`/handoff/${id}/send`, { agent_id: agentId, body }).then((r) => r.data);

export const fetchMessages = (conversationId: string): Promise<Message[]> =>
  api.get(`/dashboard/conversations/${conversationId}/messages`).then((r) => r.data);

export const fetchLeads = (stage?: string): Promise<Lead[]> =>
  api.get("/dashboard/leads", { params: stage ? { stage } : {} }).then((r) => r.data);

export const fetchCampaigns = (): Promise<Campaign[]> =>
  api.get("/campaigns").then((r) => r.data);

export const createCampaign = (data: { name: string; template_name: string; language: string }) =>
  api.post("/campaigns", data).then((r) => r.data);

export const sendCampaign = (id: string) =>
  api.post(`/campaigns/${id}/send`).then((r) => r.data);

export const uploadContacts = (id: string, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api.post(`/campaigns/${id}/contacts`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);
};
