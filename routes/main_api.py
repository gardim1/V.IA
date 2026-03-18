import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict

from routes.limpar import router as limpar_router
from routes.status import router as status_router
from routes.ver_historico import router as ver_historico_router
from services.portfolio_chat import answer_portfolio_question
from utils.rate_limit import RateLimitRule, enforce_rate_limit

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
os.makedirs("feedbacks", exist_ok=True)

load_dotenv()

CONTACT_STORAGE_FILE = Path(os.getenv("CONTACT_STORAGE_FILE", "data/contact_leads.jsonl"))
ADMIN_CONTACT_TOKEN = os.getenv("ADMIN_CONTACT_TOKEN", "").strip()
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]

CHAT_RATE_LIMIT = RateLimitRule(
    scope="chat",
    limit=int(os.getenv("RATE_LIMIT_CHAT_LIMIT", "20")),
    window_seconds=int(os.getenv("RATE_LIMIT_CHAT_WINDOW_SECONDS", "60")),
    detail="Muitas perguntas em pouco tempo. Aguarde um pouco e tente novamente.",
)
CONTACT_RATE_LIMIT = RateLimitRule(
    scope="contact",
    limit=int(os.getenv("RATE_LIMIT_CONTACT_LIMIT", "5")),
    window_seconds=int(os.getenv("RATE_LIMIT_CONTACT_WINDOW_SECONDS", "3600")),
    detail="Muitos envios de contato em pouco tempo. Tente novamente mais tarde.",
)
ADMIN_RATE_LIMIT = RateLimitRule(
    scope="admin",
    limit=int(os.getenv("RATE_LIMIT_ADMIN_LIMIT", "30")),
    window_seconds=int(os.getenv("RATE_LIMIT_ADMIN_WINDOW_SECONDS", "60")),
    detail="Muitas tentativas administrativas em pouco tempo. Tente novamente mais tarde.",
)

app = FastAPI()
app.include_router(status_router)
app.include_router(limpar_router)
app.include_router(ver_historico_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in ALLOWED_ORIGINS else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Pergunta(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"pergunta": "Me fala sobre sua carreira", "user_id": "u123"}
        }
    )

    pergunta: str
    user_id: str
    language: str | None = "pt-BR"


class ContactLead(BaseModel):
    nome: str
    empresa: str | None = ""
    email: str
    origem: str
    mensagem: str | None = ""
    idioma: str | None = "pt-BR"


def _registrar_feedback(user_id: str, pergunta_atual: str, resposta: str) -> None:
    resposta_lower = resposta.lower()
    gatilho = any(
        frase in resposta_lower
        for frase in [
            "nao encontrei",
            "nao consegui",
            "muita demanda",
            "apenas perguntas sobre vinicius",
        ]
    )

    if not gatilho:
        return

    with open("feedbacks/feedbacks.txt", "a", encoding="utf-8") as file_pointer:
        file_pointer.write(f"[Usuario]: {user_id}\n")
        file_pointer.write(f"[Pergunta atual]: {pergunta_atual.strip()}\n")
        file_pointer.write(f"[Resposta]: {resposta.strip()}\n")
        file_pointer.write("================================================================\n")


def _build_response_metadata(result, language: str | None) -> dict:
    normalized_language = "en-US" if (language or "").lower().startswith("en") else "pt-BR"
    provider = result.provider

    if provider == "openai":
        engine = "openai"
        label = "OpenAI"
        model = "gpt"
    elif provider.startswith("ollama:"):
        engine = "local"
        model = provider.split(":", 1)[1]
        label = f"Local GPU - {model}"
    elif provider == "rule":
        engine = "rules"
        label = "Fast path" if normalized_language == "en-US" else "Fluxo rapido"
        model = "rules"
    else:
        engine = "fallback"
        label = "Fallback"
        model = provider

    return {
        "provider": provider,
        "engine": engine,
        "label": label,
        "model": model,
        "used_fallback": result.used_fallback,
        "category_hint": result.category_hint,
        "rewritten_question": result.rewritten_question,
    }


def _save_contact_lead(payload: dict) -> None:
    CONTACT_STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONTACT_STORAGE_FILE.open("a", encoding="utf-8") as file_pointer:
        file_pointer.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _load_contact_leads() -> list[dict]:
    if not CONTACT_STORAGE_FILE.exists():
        return []

    items: list[dict] = []
    with CONTACT_STORAGE_FILE.open("r", encoding="utf-8") as file_pointer:
        for line in file_pointer:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _build_admin_contacts_page() -> str:
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Painel de Contatos | Vinnie</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #121212;
      --panel: #1d1d1d;
      --line: rgba(255,255,255,.1);
      --text: #f4f4f4;
      --text-soft: rgba(244,244,244,.72);
      --accent: #19c37d;
      --danger: #ff8d9b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 24px;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, Arial, sans-serif;
    }
    .shell {
      max-width: 1100px;
      margin: 0 auto;
      display: grid;
      gap: 18px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 20px;
    }
    h1, h2, p { margin: 0; }
    .intro { display: grid; gap: 8px; }
    .intro p { color: var(--text-soft); line-height: 1.6; }
    .toolbar {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
    }
    input, button {
      font: inherit;
      border-radius: 999px;
      border: 1px solid var(--line);
      padding: 12px 14px;
    }
    input {
      min-width: 280px;
      background: rgba(255,255,255,.03);
      color: var(--text);
    }
    button {
      cursor: pointer;
      background: var(--accent);
      color: #08110d;
      font-weight: 700;
    }
    .secondary {
      background: rgba(255,255,255,.05);
      color: var(--text);
      font-weight: 500;
    }
    .status {
      color: var(--text-soft);
      min-height: 22px;
    }
    .status.error { color: var(--danger); }
    .status.success { color: #92e6bd; }
    .cards {
      display: grid;
      gap: 12px;
    }
    .card {
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      background: rgba(255,255,255,.02);
      display: grid;
      gap: 10px;
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .card-header strong {
      font-size: 1.05rem;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: var(--text-soft);
      font-size: .92rem;
    }
    .empty {
      color: var(--text-soft);
      text-align: center;
      padding: 20px 12px;
    }
    @media (max-width: 680px) {
      body { padding: 14px; }
      .panel { padding: 16px; }
      input { min-width: 100%; }
      .toolbar > * { width: 100%; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="panel intro">
      <h1>Painel de contatos do Vinnie</h1>
      <p>Use seu token de administrador para listar os contatos enviados pelo portfolio. Os dados sao carregados do endpoint privado <code>/admin/contatos</code>.</p>
    </section>

    <section class="panel">
      <div class="toolbar">
        <input id="token" placeholder="Cole aqui o ADMIN_CONTACT_TOKEN" type="password" />
        <button id="loadButton" type="button">Carregar contatos</button>
        <button id="clearButton" class="secondary" type="button">Limpar</button>
      </div>
      <p id="status" class="status"></p>
    </section>

    <section class="panel">
      <h2 style="margin-bottom: 14px;">Entradas</h2>
      <div id="list" class="cards">
        <div class="empty">Nenhum contato carregado ainda.</div>
      </div>
    </section>
  </main>

  <script>
    const tokenInput = document.getElementById("token");
    const loadButton = document.getElementById("loadButton");
    const clearButton = document.getElementById("clearButton");
    const status = document.getElementById("status");
    const list = document.getElementById("list");

    function setStatus(message, tone) {
      status.textContent = message || "";
      status.className = tone ? `status ${tone}` : "status";
    }

    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function renderItems(items) {
      if (!items.length) {
        list.innerHTML = '<div class="empty">Nenhum contato recebido ainda.</div>';
        return;
      }

      list.innerHTML = items.map((item) => `
        <article class="card">
          <div class="card-header">
            <strong>${escapeHtml(item.nome)}</strong>
            <span>${escapeHtml(item.submitted_at || "")}</span>
          </div>
          <div class="meta">
            <span><strong>Empresa:</strong> ${escapeHtml(item.empresa || "-")}</span>
            <span><strong>Email:</strong> ${escapeHtml(item.email || "-")}</span>
            <span><strong>Origem:</strong> ${escapeHtml(item.origem || "-")}</span>
            <span><strong>Idioma:</strong> ${escapeHtml(item.idioma || "-")}</span>
          </div>
          <div class="meta">
            <span><strong>IP:</strong> ${escapeHtml(item.client_ip || "-")}</span>
            <span><strong>User-Agent:</strong> ${escapeHtml(item.user_agent || "-")}</span>
          </div>
          <p>${escapeHtml(item.mensagem || "Sem mensagem adicional.")}</p>
        </article>
      `).join("");
    }

    async function loadContacts() {
      const token = tokenInput.value.trim();
      if (!token) {
        setStatus("Informe o token de administrador para continuar.", "error");
        return;
      }

      setStatus("Carregando contatos...", "");
      loadButton.disabled = true;

      try {
        const response = await fetch("/admin/contatos", {
          headers: { "x-admin-token": token }
        });

        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.detail || "Nao foi possivel carregar os contatos.");
        }

        renderItems(payload.items || []);
        setStatus(`${(payload.items || []).length} contato(s) carregado(s).`, "success");
      } catch (error) {
        renderItems([]);
        setStatus(error.message || "Nao foi possivel carregar os contatos.", "error");
      } finally {
        loadButton.disabled = false;
      }
    }

    loadButton.addEventListener("click", loadContacts);
    clearButton.addEventListener("click", () => {
      tokenInput.value = "";
      renderItems([]);
      setStatus("", "");
    });
  </script>
</body>
</html>"""


@app.post("/perguntar", tags=["IA Perfil"], response_model=dict)
async def perguntar(input_data: Pergunta, request: Request, response: Response):
    try:
        enforce_rate_limit(request, response, CHAT_RATE_LIMIT)
        result = answer_portfolio_question(
            question=input_data.pergunta,
            user_id=input_data.user_id,
            language=input_data.language,
        )
        _registrar_feedback(input_data.user_id, input_data.pergunta, result.answer)
        return {"resposta": result.answer, "metadata": _build_response_metadata(result, input_data.language)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/contato", tags=["Contato"], response_model=dict)
async def registrar_contato(input_data: ContactLead, request: Request, response: Response):
    try:
        enforce_rate_limit(request, response, CONTACT_RATE_LIMIT)
        payload = {
            "nome": input_data.nome.strip(),
            "empresa": (input_data.empresa or "").strip(),
            "email": input_data.email.strip(),
            "origem": input_data.origem.strip(),
            "mensagem": (input_data.mensagem or "").strip(),
            "idioma": input_data.idioma or "pt-BR",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "client_ip": request.client.host if request.client else "",
            "user_agent": request.headers.get("user-agent", ""),
        }
        _save_contact_lead(payload)
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/admin/contatos", tags=["Contato"], response_model=dict)
async def listar_contatos(request: Request, response: Response, x_admin_token: str | None = Header(default=None)):
    enforce_rate_limit(request, response, ADMIN_RATE_LIMIT)

    if not ADMIN_CONTACT_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="ADMIN_CONTACT_TOKEN is not configured. Configure it to enable private contact viewing.",
        )

    if x_admin_token != ADMIN_CONTACT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token.")

    return {"items": list(reversed(_load_contact_leads()))}


@app.get("/admin/contatos/painel", tags=["Contato"], response_class=HTMLResponse)
async def painel_contatos(request: Request, response: Response):
    enforce_rate_limit(request, response, ADMIN_RATE_LIMIT)
    return HTMLResponse(_build_admin_contacts_page())


@app.get("/")
async def root():
    return {"resposta": "API de Perguntas e Respostas sobre Vinicius Gardim. Acesse /docs."}
