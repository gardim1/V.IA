import type { ChatMessage } from "../types";
import { RichText } from "./RichText";
import { ThinkingPanel } from "./ThinkingPanel";

interface MessageListProps {
  messages: ChatMessage[];
  loading: boolean;
  thinkingSteps: readonly string[];
  assistantLabel: string;
  thinkingSubtitle: string;
  thinkingTitle: string;
  loadingLabel: string;
  userLabel: string;
}

export function MessageList({
  messages,
  loading,
  thinkingSteps,
  assistantLabel,
  thinkingSubtitle,
  thinkingTitle,
  loadingLabel,
  userLabel
}: MessageListProps) {
  return (
    <div className="message-list">
      {messages.map((message) => (
        <article className={`message-bubble ${message.role}`} key={message.id}>
          <div className="message-meta">
            <span>{message.role === "assistant" ? assistantLabel : userLabel}</span>
            {message.role === "assistant" && message.metadata ? (
              <span className={`provider-pill ${message.metadata.engine}`}>{message.metadata.label}</span>
            ) : null}
          </div>
          <RichText content={message.content} />
        </article>
      ))}

      {loading ? (
        <article className="message-bubble assistant">
          <div className="message-meta">
            <span>{assistantLabel}</span>
            <span className="provider-pill loading">{loadingLabel}</span>
          </div>
          <ThinkingPanel steps={thinkingSteps} subtitle={thinkingSubtitle} title={thinkingTitle} />
        </article>
      ) : null}
    </div>
  );
}
