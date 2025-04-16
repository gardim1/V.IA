# 🤖 API LIA 

Esta é uma API para a assistente virtual **LIA (Logistics Intelligence Assistant)**, desenvolvida para responder dúvidas sobre o sistema TMS da Sislogica.  
A IA utiliza **RAG (Retrieval-Augmented Generation)** com base vetorial via **ChromaDB** e **LLMs locais com Ollama**.

---

## ⚙️ Requisitos

- Python 3.11+
- Ambiente virtual (recomendado)
- Dependências do projeto
- Compilador C++/C#

Instale com:

```bash
pip install -r requirements.txt
```
---
## 💻 Como rodar a API

Execute o arquivo main_api.py dentro da pasta routes com:
```bash
uvicorn routes.main_api:app --reload --port 8000
```
---
## 📂 Estrutura de pastas

```
├── .gitignore
├── chroma_langchain_db
├── delete.py
├── main.py
├── requirements.txt
├── routes
    ├── main_api.py
    ├── status.py
    └── testar.py
├── templates
    └── test_interface.html
├── test_api.py
├── update_chroma.py
├── vector.py
└── vector_utils.py
```

## 🏁 Endpoints disponíveis
| **Rota**     | **Método** | **Descrição**                                      |
|--------------|------------|-----------------------------------------------------|
| `/status`    | GET        | Verifica se a API está ativa                        |
| `/perguntar` | POST       | Envia pergunta em JSON e retorna resposta da IA     |
| `/testar`    | GET        | Abre página web para testar a IA no navegador       |
| `/docs`      | GET        | Documentação Swagger                                |

