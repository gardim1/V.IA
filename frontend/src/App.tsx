import { startTransition, useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";

import { Composer } from "./components/Composer";
import { MessageList } from "./components/MessageList";
import { QuickPrompts } from "./components/QuickPrompts";
import { Sidebar } from "./components/Sidebar";
import { ASSISTANT_NAME, DEFAULT_LANGUAGE, getUiCopy } from "./data/profile";
import { askQuestion, submitContactLead } from "./lib/api";
import type { ChatMessage, ProviderMetadata, UiLanguage } from "./types";

const SESSION_STORAGE_KEY = "via-session-id";
const LANGUAGE_STORAGE_KEY = "via-language";

function createId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getOrCreateUserId() {
  const existing = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) {
    return existing;
  }

  const created = `web-${createId()}`;
  window.localStorage.setItem(SESSION_STORAGE_KEY, created);
  return created;
}

function getStoredLanguage(): UiLanguage {
  const existing = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  return existing === "en-US" ? "en-US" : DEFAULT_LANGUAGE;
}

function buildClientErrorMessage(language: UiLanguage, error: unknown) {
  const fallback =
    language === "en-US"
      ? "I could not reach Vinnie right now."
      : "Nao foi possivel falar com o Vinnie agora.";

  if (!(error instanceof Error)) {
    return fallback;
  }

  if (error.message.includes("Backend route not found")) {
    return language === "en-US"
      ? "Backend route not found. Check the API URL or make sure FastAPI is running on port 8000."
      : "Rota do backend nao encontrada. Verifique a URL da API ou se o FastAPI esta rodando na porta 8000.";
  }

  return error.message || fallback;
}

function buildErrorMetadata(language: UiLanguage): ProviderMetadata {
  return {
    provider: "fallback_error",
    engine: "fallback",
    label: language === "en-US" ? "Connection error" : "Erro de conexao",
    model: "network",
    used_fallback: true
  };
}

export default function App() {
  const [language, setLanguage] = useState<UiLanguage>(() => getStoredLanguage());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [showPrompts, setShowPrompts] = useState(false);
  const [contactOpen, setContactOpen] = useState(false);
  const [contactSubmitting, setContactSubmitting] = useState(false);
  const [contactStatus, setContactStatus] = useState<"idle" | "success" | "error">("idle");
  const [contactForm, setContactForm] = useState({
    name: "",
    company: "",
    email: "",
    source: "linkedin",
    message: ""
  });
  const [lastProvider, setLastProvider] = useState<ProviderMetadata | undefined>();
  const userId = useMemo(() => getOrCreateUserId(), []);
  const messageViewportRef = useRef<HTMLDivElement | null>(null);
  const copy = getUiCopy(language);
  const hasConversation = messages.length > 0;
  const statusLabel = lastProvider?.label ?? copy.runtimeHint;
  const statusTone = lastProvider?.engine ?? "neutral";

  useEffect(() => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  }, [language]);

  useEffect(() => {
    if (!hasConversation || !messageViewportRef.current) {
      return;
    }

    messageViewportRef.current.scrollTo({
      top: messageViewportRef.current.scrollHeight,
      behavior: "smooth"
    });
  }, [hasConversation, isLoading, messages]);

  function handleNewChat() {
    setMessages([]);
    setInputValue("");
    setIsLoading(false);
    setLastProvider(undefined);
    setShowPrompts(false);
  }

  function openContactModal() {
    setDrawerOpen(false);
    setContactStatus("idle");
    setContactOpen(true);
  }

  function closeContactModal() {
    setContactOpen(false);
    setContactStatus("idle");
  }

  async function handleContactSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (contactSubmitting) {
      return;
    }

    setContactSubmitting(true);
    setContactStatus("idle");

    try {
      await submitContactLead({
        name: contactForm.name.trim(),
        company: contactForm.company.trim(),
        email: contactForm.email.trim(),
        source: contactForm.source,
        message: contactForm.message.trim(),
        language
      });
      setContactStatus("success");
      setContactForm({
        name: "",
        company: "",
        email: "",
        source: "linkedin",
        message: ""
      });
    } catch {
      setContactStatus("error");
    } finally {
      setContactSubmitting(false);
    }
  }

  async function submitQuestion(nextQuestion?: string) {
    const content = (nextQuestion ?? inputValue).trim();
    if (!content || isLoading) {
      return;
    }

    setShowPrompts(false);

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content
    };

    startTransition(() => {
      setMessages((current) => [...current, userMessage]);
      setInputValue("");
      setIsLoading(true);
    });

    try {
      const response = await askQuestion({ question: content, language, userId });
      const assistantMessage: ChatMessage = {
        id: createId(),
        role: "assistant",
        content: response.resposta,
        metadata: response.metadata
      };

      startTransition(() => {
        setMessages((current) => [...current, assistantMessage]);
        setLastProvider(response.metadata);
      });
    } catch (error) {
      const metadata = buildErrorMetadata(language);

      startTransition(() => {
        setMessages((current) => [
          ...current,
          {
            id: createId(),
            role: "assistant",
            content: buildClientErrorMessage(language, error),
            metadata
          }
        ]);
        setLastProvider(metadata);
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="app-rail">
        <div className="rail-group">
          <button className="rail-logo" onClick={() => setDrawerOpen(true)} title={copy.menu} type="button">
            V
          </button>
          <button className="rail-button" onClick={handleNewChat} title={copy.chatTitle} type="button">
            +
          </button>
        </div>

        <button className="rail-avatar" onClick={() => setDrawerOpen(true)} title="Vinicius Gardim" type="button">
          VG
        </button>
      </aside>

      <Sidebar
        isOpen={drawerOpen}
        language={language}
        onClose={() => setDrawerOpen(false)}
        onOpenContact={openContactModal}
      />

      <main className="workspace">
        <header className="chat-header">
          <div className="chat-header-left">
            <button className="header-menu-button" onClick={() => setDrawerOpen(true)} type="button">
              {copy.menu}
            </button>
            <div className="chat-header-brand">
              <strong>{ASSISTANT_NAME}</strong>
              <span>{copy.tagline}</span>
            </div>
          </div>

          <div className="chat-header-actions">
            <div className="language-switch">
              <span>{copy.languageToggle}</span>
              <div className="language-switch-buttons">
                <button
                  className={language === "pt-BR" ? "is-active" : ""}
                  onClick={() => setLanguage("pt-BR")}
                  type="button"
                >
                  PT
                </button>
                <button
                  className={language === "en-US" ? "is-active" : ""}
                  onClick={() => setLanguage("en-US")}
                  type="button"
                >
                  EN
                </button>
              </div>
            </div>

            <span className={`status-chip ${statusTone}`}>{statusLabel}</span>
          </div>
        </header>

        {!hasConversation ? (
          <section className="welcome-shell">
            <div className="welcome-stack">
              <div className="welcome-copy">
                <h1>{copy.emptyTitle}</h1>
                <p>{copy.emptySubtitle}</p>
              </div>

              <div className="welcome-composer">
                <Composer
                  disabled={isLoading}
                  onChange={setInputValue}
                  onSubmit={() => void submitQuestion()}
                  placeholder={copy.composerPlaceholder}
                  submitLabel={copy.send}
                  value={inputValue}
                />
              </div>

              <div className="prompt-dropdown">
                <button
                  className={`prompt-dropdown-trigger ${showPrompts ? "is-open" : ""}`}
                  onClick={() => setShowPrompts((current) => !current)}
                  type="button"
                >
                  {copy.quickPromptLabel}
                </button>

                {showPrompts ? (
                  <div className="prompt-dropdown-panel">
                    <QuickPrompts
                      disabled={isLoading}
                      onSelect={(prompt) => void submitQuestion(prompt)}
                      prompts={copy.quickPrompts}
                    />
                  </div>
                ) : null}
              </div>
            </div>
          </section>
        ) : (
          <section className="chat-stage">
            <div className="conversation-scroll" ref={messageViewportRef}>
              <MessageList
                assistantLabel={copy.assistantLabel}
                loading={isLoading}
                loadingLabel={copy.providerLoading}
                messages={messages}
                thinkingSteps={copy.thinkingSteps}
                thinkingSubtitle={copy.thinkingSubtitle}
                thinkingTitle={copy.thinkingTitle}
                userLabel={copy.userLabel}
              />
            </div>

            <div className="composer-dock">
              <Composer
                disabled={isLoading}
                onChange={setInputValue}
                onSubmit={() => void submitQuestion()}
                placeholder={copy.composerPlaceholder}
                submitLabel={copy.send}
                value={inputValue}
              />
            </div>
          </section>
        )}
      </main>

      {contactOpen ? (
        <div className="contact-modal-backdrop" onClick={closeContactModal} aria-hidden="true">
          <div className="contact-modal" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
            <div className="contact-modal-header">
              <div>
                <strong>{copy.contactTitle}</strong>
                <p>{copy.contactSubtitle}</p>
              </div>
              <button className="contact-modal-close" onClick={closeContactModal} type="button">
                {copy.close}
              </button>
            </div>

            <form className="contact-form" onSubmit={(event) => void handleContactSubmit(event)}>
              <label className="contact-field">
                <span>{copy.contactNameLabel}</span>
                <input
                  onChange={(event) => setContactForm((current) => ({ ...current, name: event.target.value }))}
                  required
                  type="text"
                  value={contactForm.name}
                />
              </label>

              <label className="contact-field">
                <span>{copy.contactCompanyLabel}</span>
                <input
                  onChange={(event) => setContactForm((current) => ({ ...current, company: event.target.value }))}
                  type="text"
                  value={contactForm.company}
                />
              </label>

              <label className="contact-field">
                <span>{copy.contactEmailLabel}</span>
                <input
                  onChange={(event) => setContactForm((current) => ({ ...current, email: event.target.value }))}
                  required
                  type="email"
                  value={contactForm.email}
                />
              </label>

              <label className="contact-field">
                <span>{copy.contactSourceLabel}</span>
                <select
                  onChange={(event) => setContactForm((current) => ({ ...current, source: event.target.value }))}
                  value={contactForm.source}
                >
                  {copy.contactSourceOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="contact-field">
                <span>{copy.contactMessageLabel}</span>
                <textarea
                  onChange={(event) => setContactForm((current) => ({ ...current, message: event.target.value }))}
                  rows={4}
                  value={contactForm.message}
                />
              </label>

              {contactStatus === "success" ? <p className="contact-feedback success">{copy.contactSuccess}</p> : null}
              {contactStatus === "error" ? <p className="contact-feedback error">{copy.contactError}</p> : null}

              <div className="contact-form-actions">
                <button className="contact-secondary" onClick={closeContactModal} type="button">
                  {copy.contactCancelLabel}
                </button>
                <button className="contact-primary" disabled={contactSubmitting} type="submit">
                  {copy.contactSubmitLabel}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
}
