# LIA – Logistics Intelligence Assistant


## Stack Principal

- **Python 3.11+**
- **FastAPI** para expor endpoints
- **Ollama** (LLMs locais como `llama3.2`, `mistral`)
- **ChromaDB** como vetorstore
- **LangGraph** para controle de fluxo entre agentes
- **Redis** para histórico de conversas por usuário
- **KeyBERT** para gerar resumos de perfil

---

## Execução Local

Requisitos:

```bash
pip install -r requirements.txt
```

Certifique-se de que o **Ollama** esteja rodando (`ollama run llama3.2`), assim como o **Redis** local.

Inicie a API com:

```bash
uvicorn routes.main_api:app --reload --port 8000
```

---

## Estrutura de Diretórios

```
RAG_SISLOGICA/
├── agents/                       # Agentes especializados por categoria
│   └── chamados_agent.py         # Categoria: CHAMADOS
│   └── cte_mdfe_agent.py         # Categoria: CTE_MDFE
│   └── devolucao_agent.py        # Categoria: DEVOLUCAO
│   └── frota_agent.py            # Categoria: FROTA
│   └── geral_agent.py            # Categoria: fallback
│   └── indenizacao_agent.py      # Categoria: INDENIZACAO
│   └── relatorios_agent.py       # Categoria: RELATORIOS
│   └── roteirizacao_agent.py     # Categoria: ROTEIRIZACAO
│   └── small_talk_agent.py       # Saudações e mensagens triviais
│   └── transportadora_agent.py   # Categoria: TRANSPORTADORA

├── conteudos_novos_8/            # Pasta de ingestão de novos .txt para o Chroma `Apenas um exemplo`
├── chroma_langchain_db/          # Base vetorial persistente
├── feedbacks/feedbacks.txt       # Armazena perguntas mal respondidas
├── graph/
│   └── langgraph_flow.py         # Define o fluxo de agentes (StateGraph)
│   └── roteador.py               # Classifica perguntas e define `next`
├── routes/                       # Rotas FastAPI
│   └── main_api.py               # Rota principal: POST /perguntar
│   └── testar.py                 # Interface HTML de teste
│   └── ver_historico.py          # Rota GET /history/{user_id}
│   └── resumo_usuario.py         # Geração de resumo via KeyBERT
│   └── formatar.py               # Formatação de resposta (usado parcialmente)
│   └── limpar.py                 # Reseta histórico Redis (temporário)
│   └── status.py                 # Rota de saúde da API
├── templates/test_interface.html # Frontend para teste manual
├── utils/
│   └── history_chain.py          # Utilitário para histórico com `wrap_with_history`
│   └── history.py                # RedisChatMessageHistory e TTL
├── vector_utils.py               # Vetorização, chunking, embedding e reranking
├── update_chroma.py              # Ingestão de novos documentos no Chroma
├── requirements.txt
└── .env
```

---

## Atualizar Base de Conhecimento

Para atualizar os documentos usados no RAG:

1. Coloque os arquivos `.txt` na pasta, ex: `conteudos_novos_8/`
2. Rode:

```bash
python update_chroma.py
```

---

## Funcionamento Interno

1. A pergunta do usuário é classificada via prompt (`mistral:7b`) → rota para categoria correta
2. O agente correspondente busca documentos via **ChromaDB** e faz **rerank com BAAI/bge-reranker**
3. O prompt do agente gera uma resposta estruturada (com passo a passo, validações etc)
4. A resposta é retornada e o histórico é salvo em Redis (por `user_id`)
5. Se a IA falhar (resposta vazia, genérica, etc), a pergunta é salva em `feedbacks.txt`

---

## Endpoints

| Método | Rota               | Descrição                                   |
|--------|--------------------|----------------------------------------------|
| GET    | `/status`          | Verifica se a API está ativa                 |
| POST   | `/perguntar`       | Envia pergunta com `pergunta` e `user_id`    |
| GET    | `/history/{id}`    | Retorna mensagens anteriores do usuário      |
| GET    | `/testar`          | Interface web de testes                      |
| GET    | `/docs`            | Interface Swagger                            |

---

## Observações

- O arquivo `vector.py` está obsoleto → utilizar `vector_utils.py`
- A pasta `conteudos_novos_X` é mantida apenas por histórico
- O `.env` precisa conter `REDIS_URL` e `CHAT_TTL_SECONDS` se o Redis não for padrão

