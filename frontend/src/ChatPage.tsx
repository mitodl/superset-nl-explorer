import React, { useState, useEffect, useRef } from "react";

interface PageContext {
  page?: string;
  datasource?: string | null;
  dashboard?: string | null;
  user?: string | null;
  org?: Record<string, unknown>;
}


  role: "user" | "assistant";
  content: string;
}

interface ChartAction {
  type: "explore_link" | "chart_created" | "dashboard_created";
  explore_url?: string;
  chart_url?: string;
  dashboard_url?: string;
  chart_name?: string;
  dashboard_title?: string;
}

interface AssistantMessage extends Message {
  role: "assistant";
  actions?: ChartAction[];
}

type ConversationMessage = Message | AssistantMessage;

const API_BASE = "/api/v1/nl_explorer";

export default function ChatPage() {
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [datasetId, setDatasetId] = useState<number | null>(null);
  const [pageContext, setPageContext] = useState<PageContext>({});
  const pageContextRef = useRef<PageContext>({});

  // Receive page context from the parent Superset frame via postMessage
  useEffect(() => {
    const handler = (e: MessageEvent) => {
      if (e.origin !== window.location.origin) return;
      if (e.data?.type === "NL_EXPLORER_CONTEXT") {
        pageContextRef.current = e.data.payload as PageContext;
        setPageContext(e.data.payload as PageContext);
      }
    };
    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, []);

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
          dataset_id: datasetId,
          page_context: pageContextRef.current,
          stream: false,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      const assistantMsg: AssistantMessage = {
        role: "assistant",
        content: data.message || "",
        actions: data.actions || [],
      };
      setConversation([...nextConversation, assistantMsg]);
    } catch (err) {
      const errMsg: AssistantMessage = {
        role: "assistant",
        content: `Error: ${err instanceof Error ? err.message : String(err)}`,
      };
      setConversation([...nextConversation, errMsg]);
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
    <div style={styles.page}>
      <div style={styles.header}>
        <h1 style={styles.title}>Ask Data</h1>
        <p style={styles.subtitle}>
          Explore your data and create charts using natural language.
        </p>
        {(pageContext.dashboard || pageContext.datasource) && (
          <p style={styles.contextBadge}>
            📍 Context:{" "}
            {pageContext.dashboard
              ? `Dashboard — ${pageContext.dashboard}`
              : `Dataset — ${pageContext.datasource}`}
          </p>
        )}
      </div>

      <div style={styles.chatArea}>
        {conversation.length === 0 && (
          <div style={styles.empty}>
            <p>Ask a question about your data to get started.</p>
            <p style={styles.exampleLabel}>Examples:</p>
            <ul style={styles.examples}>
              <li>"Show me total revenue by month for 2024"</li>
              <li>"Which products have the highest return rate?"</li>
              <li>"Create a bar chart of signups by country"</li>
            </ul>
          </div>
        )}

        {conversation.map((msg, idx) => (
          <div
            key={idx}
            style={msg.role === "user" ? styles.userBubble : styles.assistantBubble}
          >
            <strong>{msg.role === "user" ? "You" : "Assistant"}</strong>
            <p style={{ margin: "4px 0 0" }}>{msg.content}</p>
            {"actions" in msg &&
              msg.actions?.map((action, aIdx) => (
                <div key={aIdx} style={styles.actionCard}>
                  {action.type === "explore_link" && action.explore_url && (
                    <a href={action.explore_url} target="_blank" rel="noreferrer" style={styles.link}>
                      🔍 Open in Explore
                    </a>
                  )}
                  {action.type === "chart_created" && action.chart_url && (
                    <a href={action.chart_url} target="_blank" rel="noreferrer" style={styles.link}>
                      📊 View Chart: {action.chart_name}
                    </a>
                  )}
                  {action.type === "dashboard_created" && action.dashboard_url && (
                    <a href={action.dashboard_url} target="_blank" rel="noreferrer" style={styles.link}>
                      📋 View Dashboard: {action.dashboard_title}
                    </a>
                  )}
                </div>
              ))}
          </div>
        ))}

        {loading && (
          <div style={styles.assistantBubble}>
            <em>Thinking…</em>
          </div>
        )}
      </div>

      <div style={styles.inputArea}>
        <textarea
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your data… (Enter to send, Shift+Enter for newline)"
          rows={3}
          disabled={loading}
        />
        <button style={styles.button} onClick={sendMessage} disabled={loading || !input.trim()}>
          {loading ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    maxWidth: 800,
    margin: "0 auto",
    padding: "0 16px",
    fontFamily: "sans-serif",
  },
  header: { padding: "24px 0 8px" },
  title: { margin: 0, fontSize: 24 },
  subtitle: { color: "#666", margin: "4px 0 0" },
  chatArea: {
    flex: 1,
    overflowY: "auto",
    padding: "16px 0",
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  contextBadge: {
    fontSize: 12,
    color: "#1677ff",
    background: "#e8f0fe",
    borderRadius: 6,
    padding: "2px 8px",
    display: "inline-block",
    marginTop: 6,
  },
  empty: { color: "#888", textAlign: "center", marginTop: 64 },
  exampleLabel: { fontWeight: "bold", marginTop: 24 },
  examples: { textAlign: "left", display: "inline-block" },
  userBubble: {
    alignSelf: "flex-end",
    background: "#e8f0fe",
    borderRadius: 12,
    padding: "10px 14px",
    maxWidth: "75%",
  },
  assistantBubble: {
    alignSelf: "flex-start",
    background: "#f5f5f5",
    borderRadius: 12,
    padding: "10px 14px",
    maxWidth: "85%",
  },
  actionCard: {
    marginTop: 8,
    padding: "8px 12px",
    background: "#fff",
    borderRadius: 8,
    border: "1px solid #ddd",
  },
  link: { color: "#1677ff", textDecoration: "none" },
  inputArea: {
    display: "flex",
    gap: 8,
    padding: "12px 0 24px",
    borderTop: "1px solid #e0e0e0",
  },
  input: {
    flex: 1,
    padding: "10px 12px",
    borderRadius: 8,
    border: "1px solid #ccc",
    resize: "none",
    fontSize: 14,
  },
  button: {
    padding: "0 20px",
    borderRadius: 8,
    border: "none",
    background: "#1677ff",
    color: "#fff",
    fontWeight: "bold",
    cursor: "pointer",
    fontSize: 14,
  },
};
