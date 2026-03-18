export type ChatRole = "assistant" | "user";
export type UiLanguage = "pt-BR" | "en-US";

export interface ProviderMetadata {
  provider: string;
  engine: "openai" | "local" | "rules" | "fallback" | string;
  label: string;
  model: string;
  used_fallback: boolean;
  category_hint?: string | null;
  rewritten_question?: string | null;
}

export interface AskResponse {
  resposta: string;
  metadata?: ProviderMetadata;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  metadata?: ProviderMetadata;
}

export interface SidebarLink {
  label: string;
  href: string;
  description: string;
  external?: boolean;
  download?: boolean | string;
  ctaLabel?: string;
  kind?: "contact";
  placeholder?: boolean;
}

export interface SidebarCard {
  title: string;
  eyebrow: string;
  description: string;
  href?: string;
  external?: boolean;
  download?: boolean | string;
  ctaLabel?: string;
  note?: string;
}
