
import React, { useState, useRef, useEffect } from "react";
import "./ExpenseChatbot.css";

const API_URL = "http://localhost:9005/chatbot/";

type MessageRole = "user" | "assistant";

interface ChatMessage {
  role: MessageRole;
  content: string;
  error?: boolean;
}

interface ChatApiResponse {
  response?: unknown;
  message?: unknown;
  answer?: unknown;
  result?: unknown;
}

export default function ExpenseChatbot(): React.JSX.Element {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hello! 👋 I'm your personal expense assistant. Ask me anything about your spending, expenses, or budget.",
    },
  ]);

  const [prompt, setPrompt] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const sendMessage = async (): Promise<void> => {
    const question = prompt.trim();

    if (!question || loading) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
    ]);

    setPrompt("");
    setLoading(true);

    try {
      const url = API_URL+`?query=${question}`
      //const response = await fetch(url);

      const response = await  fetch(url, {
      method: "GET",
      headers: {
        "Access-Control-Allow-Origin": `*`, // access control header
        "Content-Type": "application/json"
      },
      credentials: "include" // send cookies if needed
    })
    //const s_res = await response.json()
    //console.log('Server response: ',s_res)
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data: ChatApiResponse = await response.json();

      const answer =
        data.response ??
        data.message ??
        data.answer ??
        data.result ??
        "The server returned an empty response.";

      const content =
        typeof answer === "string"
          ? answer
          : JSON.stringify(answer, null, 2) ?? "";

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content,
        },
      ]);
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "An unexpected error occurred.";

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, something went wrong: ${errorMessage}. Please check whether your API server is running.`,
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLTextAreaElement>
  ): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  };

  const suggestions: string[] = [
    "How much did I spend this month?",
    "Show my top spending categories",
    "Where can I reduce expenses?",
    "Summarize my monthly expenses",
  ];

  return (
    <div className="expense-app">
      <aside className="expense-sidebar">
        <div className="brand">
          <span className="brand-icon">₹</span>
          <span>Expense AI</span>
        </div>

        <div className="sidebar-section">
          <p className="sidebar-label">YOUR ASSISTANT</p>

          <div className="sidebar-item active">
            <span>💬</span> Expense Chat
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="profile">
            <div className="avatar">U</div>
            <div>
              <strong>My Account</strong>
              <small>Personal Finance</small>
            </div>
          </div>
        </div>
      </aside>

      <main className="chat-main">
        <header className="chat-header">
          <div>
            <h2>Personal Expense Assistant</h2>
            <p>Ask questions about your finances</p>
          </div>

          <div className="status">
            <span className="status-dot"></span>
            AI Assistant
          </div>
        </header>

        <section className="chat-messages">
          {messages.length === 1 && (
            <div className="welcome">
              <div className="welcome-icon">💰</div>

              <h1>Take control of your expenses.</h1>

              <p>
                Ask me questions about your spending habits,
                monthly expenses, budgets, and savings.
              </p>

              <div className="suggestions">
                {suggestions.map((item) => (
                  <button
                    key={item}
                    onClick={() => setPrompt(item)}
                  >
                    {item} <span>→</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="message-list">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`message-row ${message.role}`}
              >
                {message.role === "assistant" && (
                  <div className="message-avatar">₹</div>
                )}

                <div
                  className={`message-bubble ${
                    message.error ? "error" : ""
                  }`}
                >
                  <div className="message-author">
                    {message.role === "user"
                      ? "You"
                      : "Expense Assistant"}
                  </div>

                  <div className="message-content">
                    {message.content}
                  </div>
                </div>

                {message.role === "user" && (
                  <div className="user-avatar">U</div>
                )}
              </div>
            ))}

            {loading && (
              <div className="message-row assistant">
                <div className="message-avatar">₹</div>

                <div className="message-bubble">
                  <div className="message-author">
                    Expense Assistant
                  </div>

                  <div className="typing">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>
        </section>

        <footer className="chat-footer">
          <div className="input-container">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your expenses..."
              rows={1}
              disabled={loading}
            />

            <button
              className="send-button"
              onClick={() => void sendMessage()}
              disabled={!prompt.trim() || loading}
              aria-label="Send message"
            >
              ↑
            </button>
          </div>

          <p className="footer-hint">
            Press Enter to send · Shift + Enter for a new line
          </p>
        </footer>
      </main>
    </div>
  );
}
