import React, { useState } from "react";

interface ChatPanelProps {
  /** Superset dataset ID to scope the conversation. Passed by Explore view. */
  datasetId?: number;
  /** Superset dashboard ID to scope the conversation. Passed by Dashboard view. */
  dashboardId?: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
}

const API_BASE = "/api/v1/extensions/nl_explorer";

/**
 * Floating collapsible chat panel injected into Explore and Dashboard views
 * via the Superset extension contribution API.
 */
export default function ChatPanel({ datasetId, dashboardId }: ChatPanelProps) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [conversation, setConversation] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: "user", content: input };
    const nextConversation = [...conversation, userMsg];
    setConversation(nextConversation);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          message: input,
          conversation: nextConversation,
          dataset_id: datasetId ?? null,
          dashboard_id: dashboardId ?? null,
          stream: false,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setConversation([
        ...nextConversation,
        { role: "assistant", content: data.message || "" },
      ]);
    } catch (err) {
      setConversation([
        ...nextConversation,
        {
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : String(err)}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={styles.container}>
      {/* Toggle button */}
      <button style={styles.toggle} onClick={() => setOpen((o) => !o)} title="Ask Data">
        💬 Ask Data
      </button>

      {open && (
        <div style={styles.panel}>
          <div style={styles.panelHeader}>
            <span style={{ fontWeight: "bold" }}>Ask Data</span>
            <button style={styles.close} onClick={() => setOpen(false)}>
              ✕
            </button>
          </div>

          <div style={styles.messages}>
            {conversation.length === 0 && (
              <p style={styles.placeholder}>
                {datasetId
                  ? "Ask a question about this dataset…"
                  : "Ask a question about your data…"}
              </p>
            )}
            {conversation.map((msg, idx) => (
              <div
                key={idx}
                style={msg.role === "user" ? styles.userMsg : styles.assistantMsg}
              >
                {msg.content}
              </div>
            ))}
            {loading && <div style={styles.assistantMsg}><em>Thinking…</em></div>}
          </div>

          <div style={styles.inputRow}>
            <input
              style={styles.input}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask…"
              disabled={loading}
            />
            <button
              style={styles.sendBtn}
              onClick={sendMessage}
              disabled={loading || !input.trim()}
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    position: "fixed",
    bottom: 24,
    right: 24,
    zIndex: 1000,
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
    gap: 8,
    fontFamily: "sans-serif",
  },
  toggle: {
    padding: "10px 16px",
    borderRadius: 24,
    border: "none",
    background: "#1677ff",
    color: "#fff",
    fontWeight: "bold",
    cursor: "pointer",
    boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
    fontSize: 14,
  },
  panel: {
    width: 340,
    height: 460,
    background: "#fff",
    borderRadius: 12,
    boxShadow: "0 4px 24px rgba(0,0,0,0.15)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  panelHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 14px",
    borderBottom: "1px solid #eee",
    background: "#fafafa",
  },
  close: {
    background: "none",
    border: "none",
    cursor: "pointer",
    fontSize: 14,
    color: "#888",
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: 12,
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  placeholder: { color: "#aaa", fontSize: 13, textAlign: "center", margin: "auto" },
  userMsg: {
    alignSelf: "flex-end",
    background: "#e8f0fe",
    borderRadius: 10,
    padding: "8px 12px",
    fontSize: 13,
    maxWidth: "80%",
  },
  assistantMsg: {
    alignSelf: "flex-start",
    background: "#f0f0f0",
    borderRadius: 10,
    padding: "8px 12px",
    fontSize: 13,
    maxWidth: "85%",
  },
  inputRow: {
    display: "flex",
    gap: 6,
    padding: "10px 12px",
    borderTop: "1px solid #eee",
  },
  input: {
    flex: 1,
    padding: "8px 10px",
    borderRadius: 8,
    border: "1px solid #ccc",
    fontSize: 13,
  },
  sendBtn: {
    padding: "0 12px",
    borderRadius: 8,
    border: "none",
    background: "#1677ff",
    color: "#fff",
    cursor: "pointer",
    fontSize: 16,
  },
};
