# Vinnie | AI Portfolio Backend + Frontend

Portfolio conversacional do Vinicius Silva Gardim.

O projeto e dividido em duas partes:

- `frontend/`: interface React + Vite para recrutadores e visitantes
- `backend`: API FastAPI com RAG, fallback de providers, historico e painel simples de contatos

## Visao geral

O Vinnie e o assistente virtual do portfolio do Vinicius. Ele responde perguntas sobre carreira, projetos, stack, objetivos, forma de trabalho e outros temas pessoais/profissionais que estejam na base documental.

Fluxo principal:

1. o frontend envia a pergunta para `POST /perguntar`
2. o backend busca contexto no Chroma
3. tenta responder via OpenAI
4. se OpenAI falhar, tenta provider local via Ollama
5. se tudo falhar, devolve uma mensagem amigavel

## Estrutura

- `routes/main_api.py`: API principal, contatos, painel admin, CORS e rate limit
- `services/portfolio_chat.py`: fluxo central de pergunta/resposta
- `vector_utils.py`: retrieval, categorizacao e persistencia vetorial
- `update_chroma.py`: recria a base vetorial a partir de `conteudos_vini_02/`
- `utils/history.py`: historico em Redis com fallback para memoria
- `utils/rate_limit.py`: rate limit com Redis e fallback para memoria
- `frontend/src/`: app React

## Requisitos

- Python 3.11+
- Node 22+
- Redis
- Ollama
- chave da OpenAI

## Variaveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores:

```bash
copy .env.example .env
```

Variaveis mais importantes:

- `OPENAI_API_KEY`: chave da OpenAI
- `OPENAI_MODEL`: modelo principal
- `OPENAI_EMBED_MODEL`: modelo de embedding da OpenAI
- `EMBED_PROVIDER`: `openai` ou `ollama`
- `OLLAMA_BASE_URL`: endpoint do Ollama
- `OLLAMA_RAG_MODEL`: modelo local de fallback
- `OLLAMA_EMBED_MODEL`: modelo de embedding
- `REDIS_URL`: Redis para historico e rate limit
- `ADMIN_CONTACT_TOKEN`: token para acessar os contatos privados
- `ALLOWED_ORIGINS`: dominios autorizados no CORS, separados por virgula

## Base vetorial

Os documentos usados pelo RAG ficam em `conteudos_vini_02/`.

Para recriar a base do zero:

```bash
python update_chroma.py
```

O script remove a base anterior, recarrega os `.txt` validos e reconstrui o Chroma.

Para deploy em cloud sem Ollama no servidor, use:

```bash
EMBED_PROVIDER=openai
OPENAI_EMBED_MODEL=text-embedding-3-small
```

Assim o backend pode reconstruir e consultar a base vetorial usando a OpenAI, sem depender de Ollama para embeddings.

## Rodando localmente sem Docker

Backend:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python update_chroma.py
uvicorn routes.main_api:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

No `frontend/.env.local`, defina:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Rodando com Docker + Redis

O projeto agora tem `docker-compose.yml` para subir backend e Redis juntos.

```bash
docker compose up --build
```

Isso sobe:

- `backend` na porta `8000`
- `redis` na porta `6379`

Observacoes importantes:

- o frontend nao sobe nesse compose; ele continua separado porque, em producao, a ideia e publica-lo na Vercel
- se o backend no container precisar conversar com um Ollama rodando na sua maquina host, use algo como:

```bash
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

- no Dockerfile de producao, o backend executa `python update_chroma.py` antes de subir a API, para recriar a base vetorial automaticamente no ambiente cloud

## Endpoints principais

- `POST /perguntar`: pergunta principal do chat
- `POST /contato`: salva lead de contato
- `GET /status`: healthcheck completo
- `GET /status/openai`
- `GET /status/local`
- `GET /status/redis`
- `GET /status/vector`
- `GET /admin/contatos`: lista contatos salvos, exige `x-admin-token`
- `GET /admin/contatos/painel`: painel HTML simples para visualizar contatos

## Rate limit e seguranca

Ja foi adicionado:

- rate limit em `/perguntar`
- rate limit em `/contato`
- rate limit nas rotas administrativas
- CORS configuravel por `ALLOWED_ORIGINS`
- token administrativo em `ADMIN_CONTACT_TOKEN`

Configuracoes padrao:

- chat: `20` req por `60s`
- contato: `5` req por `3600s`
- admin: `30` req por `60s`

Se Redis estiver disponivel, o rate limit usa Redis.
Se Redis nao estiver disponivel, cai para memoria local.

## Contatos privados

Os contatos enviados pelo formulario ficam em:

- `data/contact_leads.jsonl`

Para consumir via API:

```http
GET /admin/contatos
x-admin-token: SEU_TOKEN
```

Para abrir o painel no navegador:

- acesse `/admin/contatos/painel`
- informe o token

## Frontend em producao

Recomendacao:

- publique o `frontend/` na Vercel
- aponte `VITE_API_BASE_URL` para o backend publicado

Se quiser reaproveitar um projeto Vercel existente, configure a `Root Directory` como:

```text
frontend
```

## Backend em producao

Opcoes praticas:

- Railway para o backend principal
- fallback local via Ollama, se voce quiser manter esse plano

Arquitetura recomendada para deploy hibrido:

1. frontend na Vercel
2. backend principal na Railway
3. OpenAI como provider principal
4. OpenAI embeddings no cloud
5. Ollama local como fallback opcional

Se voce quiser usar fallback local real em producao, sua maquina e o servico do Ollama precisam estar ligados quando esse fallback for necessario.

## Testes

Backend:

```bash
python -m pytest -q -p no:tmpdir
```

Frontend:

```bash
cd frontend
npm run build
```

## Estado atual

Validado nesta base:

- testes backend passando
- build do frontend passando
- base Chroma recriada com os documentos atuais

