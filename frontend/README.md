# Frontend Vinnie

Interface React + Vite para o portfolio conversacional do Vinicius.

## Requisitos

- Node 22+
- Backend FastAPI rodando

## Ambiente

Crie um arquivo `.env.local` em `frontend/` com:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Se o frontend e o backend estiverem servidos no mesmo dominio, voce pode deixar esse valor vazio e usar rotas relativas.

## Rodar localmente

```bash
npm install
npm run dev
```

## Build de producao

```bash
npm run build
```

## Estrutura

- `src/App.tsx`: shell principal da experiencia
- `src/components/`: sidebar, composer, prompts e timeline de loading
- `src/data/profile.ts`: cards, perguntas rapidas e links
- `src/lib/api.ts`: integracao com o backend
