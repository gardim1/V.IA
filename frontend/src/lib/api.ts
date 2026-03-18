import type { AskResponse } from "../types";

function resolveApiBaseUrl() {
  const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").trim().replace(/\/$/, "");
  if (configuredBaseUrl) {
    return configuredBaseUrl;
  }

  if (typeof window !== "undefined") {
    const { hostname, protocol, port } = window.location;
    const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1";
    const isPrivateIpv4 =
      /^10\./.test(hostname) ||
      /^192\.168\./.test(hostname) ||
      /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname);
    const isLocalNetwork = isLocalhost || isPrivateIpv4 || hostname.endsWith(".local");

    if (isLocalNetwork && port !== "8000") {
      return `${protocol}//${hostname}:8000`;
    }
  }

  return "";
}

const API_BASE_URL = resolveApiBaseUrl();

function buildUrl(path: string) {
  if (!API_BASE_URL) {
    return path;
  }

  return `${API_BASE_URL}${path}`;
}

export async function askQuestion(input: {
  question: string;
  userId: string;
  language: string;
  signal?: AbortSignal;
}): Promise<AskResponse> {
  const response = await fetch(buildUrl("/perguntar"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      pergunta: input.question,
      user_id: input.userId,
      language: input.language
    }),
    signal: input.signal
  });

  if (!response.ok) {
    let detail = "Nao foi possivel enviar a pergunta.";
    try {
      const payload = await response.json();
      detail = payload.detail ?? detail;
    } catch {
      detail = response.statusText || detail;
    }

    if (response.status === 404) {
      detail =
        "Backend route not found. Check VITE_API_BASE_URL or make sure the FastAPI server is running on port 8000.";
    }

    throw new Error(detail);
  }

  return (await response.json()) as AskResponse;
}

export async function submitContactLead(input: {
  name: string;
  company: string;
  email: string;
  source: string;
  message: string;
  language: string;
}): Promise<{ status: string }> {
  const response = await fetch(buildUrl("/contato"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      nome: input.name,
      empresa: input.company,
      email: input.email,
      origem: input.source,
      mensagem: input.message,
      idioma: input.language
    })
  });

  if (!response.ok) {
    let detail = "Nao foi possivel enviar o contato.";
    try {
      const payload = await response.json();
      detail = payload.detail ?? detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }

  return (await response.json()) as { status: string };
}
