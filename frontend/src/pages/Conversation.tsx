import React, { useEffect, useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchMessages, agentSend, Message } from "../api/client";

const AGENT_ID = "agent-001";

interface Props {
  conversationId: string;
  handoffId: string;
  leadPhone: string;
  onClose?: () => void;
}

export default function Conversation({ conversationId, handoffId, leadPhone, onClose }: Props) {
  const qc = useQueryClient();
  const endRef = useRef<HTMLDivElement>(null);
  const [draft, setDraft] = useState("");

  const { data: messages = [] } = useQuery<Message[]>({
    queryKey: ["messages", conversationId],
    queryFn: () => fetchMessages(conversationId),
    refetchInterval: 5000,
  });

  const sendMut = useMutation({
    mutationFn: (body: string) => agentSend(handoffId, AGENT_ID, body),
    onSuccess: () => {
      setDraft("");
      qc.invalidateQueries({ queryKey: ["messages", conversationId] });
    },
  });

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const text = draft.trim();
    if (!text) return;
    sendMut.mutate(text);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <div>
          <span className="font-medium text-gray-900">{leadPhone}</span>
          <span className="ml-2 text-xs text-gray-400">WhatsApp</span>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-xl leading-none">
            ×
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#f0f2f5]">
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="flex items-end gap-2 p-3 border-t bg-white">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          rows={2}
          placeholder="Type a message..."
          className="flex-1 resize-none border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
        <button
          onClick={handleSend}
          disabled={!draft.trim() || sendMut.isPending}
          className="bg-indigo-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50 hover:bg-indigo-700"
        >
          Send
        </button>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isOut = message.direction === "OUT";
  return (
    <div className={`flex ${isOut ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm ${
          isOut
            ? "bg-indigo-600 text-white rounded-tr-sm"
            : "bg-white text-gray-900 shadow-sm rounded-tl-sm"
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{message.body}</p>
        <p className={`text-[10px] mt-1 ${isOut ? "text-indigo-200 text-right" : "text-gray-400"}`}>
          {new Date(message.created_at).toLocaleTimeString("en-IN", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}
