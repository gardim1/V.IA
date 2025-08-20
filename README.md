# RAG_SISLOGICA — LIA

Documento focado em **como a IA funciona**, **LangGraph + LangChain**, **agentes**, **APIs/endpoints** e **operação** (rodar local/Docker, dependências, `.env`).

## 1) Arquitetura & Fluxo
- **Entrada**: `POST /perguntar` com `pergunta` e `user_id`.
- **Roteador (LangGraph)**: classifica a pergunta (CTE/MDF-e, Frota, Chamados, etc.) e direciona para o agente.
- **RAG**: retriever (ChromaDB + embeddings Ollama) busca trechos relevantes; **reranker** reordena evidências.
- **Geração**: agente monta o prompt (LangChain) e chama o **LLM** (Ollama: llama3.2:latest, mistral:7b, mxbai-embed-large).
- **Histórico**: mensagens por `user_id` são salvas no Redis; TTL configurável.
- **Pós-processo**: endpoint `/formatar` permite padronizar a resposta final com título/caminho/campos/observações.

Fluxo (simplificado):
```
Usuário → /perguntar → LangGraph.roteador → agente_X
         → (retriever Chroma → reranker) → LLM → resposta
         → (/formatar opcional) → histórico Redis → retorno
```

### Componentes principais
- `graph/langgraph_flow.py`, `graph/roteador.py`, `graph/continuacao.py`
- `agents/*.py` (10 agentes de domínio)
- `vector.py`, `vector_utils.py` (indexação/consulta vetorial)
- `utils/history.py` (Redis), `utils/summary.py`
- `routes/*.py` (FastAPI)

### Retriever & RAG
- **Embeddings**: `OllamaEmbeddings(model="mxbai-embed-large")`
- **Chunking**: `RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=400)`
- **Top-k inicial**: `k=30` (após isso, reranqueia)
- **Reranker**: `BAAI/bge-reranker-large` (via `sentence-transformers`)
- **Coleção Chroma**: `ajuda_sislogica` em `./chroma_langchain_db`

## 2) Agentes disponíveis
- `chamados_agent`
- `cte_mdfe_agent`
- `devolucao_agent`
- `frota_agent`
- `geral_agent`
- `indenizacao_agent`
- `relatorios_agent`
- `roteirizacao_agent`
- `small_talk_agent`
- `transportadora_agent`

## 3) APIs & Endpoints
| Método | Caminho | Arquivo |
|---|---|---|
| GET | `/` | main_api.py |
| POST | `/formatar` | formatar.py |
| DELETE | `/history/{user_id}` | limpar.py |
| GET | `/history/{user_id}` | ver_historico.py |
| POST | `/perguntar` | main_api.py |
| GET | `/status` | status.py |
| GET | `/testar` | testar.py |
| GET | `/usuario/{user_id}/resumo` | resumo_usuario.py |

### Contratos importantes
**POST `/perguntar`** — Body:
```json
{
  "pergunta": "<string>",
  "user_id": "<string>"
}
```
Resposta:
```json
{ "resposta": "..." }
```

**POST `/formatar`** — Body (`FeedbackCompleto`):
```json
{
  "pergunta_atual": "<string>",
  "pergunta_anterior": "<string>",
  "resposta_correta": "<string>"
}
```
Retorna um texto já padronizado (título, caminho, como realizar, campos, observações).

**GET `/status`** → healthcheck

**GET `/testar`** → página HTML simples para testar a IA

**GET `/history/{user_id}`** → recupera histórico do usuário

**DELETE `/history/{user_id}`** → apaga histórico do usuário

**GET `/usuario/{user_id}/resumo`** → resumo condensado do histórico

## 4) Como rodar
### Local (sem Docker)
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn routes.main_api:app --reload --host 0.0.0.0 --port 8000
```
- Instale e rode **Ollama** no host (porta padrão `11434`).
- Baixe os modelos usados:
```bash
ollama pull mistral:7b
ollama pull llama3.2:latest
ollama pull mxbai-embed-large
```
- Inicie **Redis** (local ou via Docker):
```bash
docker run -p 6379:6379 redis:7
```

### Docker / Compose
`docker-compose.yml` já sobe **api** e **redis**:
```bash
docker compose up --build
```
_Observação_: o serviço ainda espera um servidor **Ollama** acessível (ex.: `host.docker.internal:11434`). Se necessário, defina `OLLAMA_HOST=http://host.docker.internal:11434` no `.env`.

## 5) Configuração (.env)
- `REDIS_URL` (ex.: `redis://localhost:6379`)
- `CHAT_TTL_SECONDS` (ex.: `2592000`)
- `ENV` (ex.: `dev`/`prod`)
- `SERVER` (opcional; usado em `db_utils.py` se habilitar SQL Server por env)
- (opcionais) `OLLAMA_HOST`, variáveis de DB (`UID`, `PWD`, `DATABASE`) se for usar SQL Server autenticado)

## 6) Dependências (requirements)
- fastapi
- uvicorn
- langchain
- langchain-community
- langchain-core
- langchain-chroma
- langchain-ollama
- pydantic
- pytest
- httpx
- jinja2
- langchain-text-splitters
- redis
- python-dotenv
- pyodbc
- keybert
- stop-words
- langgraph

## 7) Indexação & Atualização do Chroma
- **Atualizar a coleção** com pastas de `.txt`: `python vector.py` (função `update_chroma_from_folder`) ou `python update_chroma.py`.
- Pastas de conteúdo detectadas (exemplo):
  - `cconteudos_novos_9/`
    
*Passar caminho da pasta desejada no arquivo `update_chroma.py`*

## 8) Histórico & Resumos
- `utils/history.py` usa `RedisChatMessageHistory` (TTL via `CHAT_TTL_SECONDS`).
- `utils/summary.py` gera resumos periódicos para manter o contexto enxuto.

## 9) Dicas de manutenção
- Monitore latência do retriever e do `reranker` (pode ser pesado). Ajuste `k`, `chunk_size/overlap`.
- Log estruturado e captura de exceções (ver `try/except` nos endpoints).
- Versione prompts dos agentes em `agents/templates.py`.
- Adicione testes para `/perguntar` e para o roteador do LangGraph.

