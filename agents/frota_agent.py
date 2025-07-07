from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_utils import get_retriever
from vector_utils import get_retriever, rerank_docs

def frota_agent(state: dict) -> dict:
    pergunta = state["pergunta"]

    retriever = get_retriever(filtro="FROTA")
    docs = retriever.invoke(pergunta)
    docs = rerank_docs(pergunta, docs, top_k=3)
    contexto = "\n".join(d.page_content for d in docs) if docs else ""

    print("\n=== [FROTA] Chunks recuperados individualmente ===")
    for i, d in enumerate(docs, 1):
        print(f"Doc {i}:\n{d.page_content}\n")

    contexto = "\n".join(d.page_content for d in docs)

    print("\n=== [FROTA] Texto total passado para IA ===")
    print(contexto)
    print("===================================================\n")

    prompt = ChatPromptTemplate.from_template(
    """
##############################
# CONTEXTO INTERNO — NÃO MOSTRAR AO USUÁRIO
##############################
Você é a **LIA** (Logistics Intelligence Assistant) especialista na categoria {categoria}.
Responda **exclusivamente** com base nos DOCUMENTOS DE REFERÊNCIA abaixo.

##############################
# DOCUMENTOS DE REFERÊNCIA
##############################
{docs}

##############################
# PERGUNTA DO USUÁRIO
##############################
{pergunta}

##############################
# INSTRUÇÕES DE RESPOSTA
##############################
1. **Use apenas** o conteúdo de {docs}.  
2. Se a informação não existir, responda **exatamente**:  
   "Desculpe, não encontrei essa informação nos documentos disponíveis."
3. **Precisão técnica**  
   • Cite nomes exatos de menus, telas, botões e campos.  
   • Mostre o caminho completo de navegação.  
4. **Estrutura obrigatória**  
   **[Título Direto]**  
   **Passo a Passo**  
   1. …  
   **Validações Antes de Finalizar**  
   - …  
   **Se Algo Der Errado** (apenas se mencionado nos docs)  
   - …  
   **Onde Obter Ajuda** (apenas se mencionado nos docs)  
   - …  
5. **Formatação**  
   - Use `backticks` para elementos de UI.  
   - Títulos em **negrito**.  
   - Máximo 2 emojis relevantes (✅ ⚠️).  
6. **Proibições**  
   - Nunca invente dados ou faça suposições.  
   - Não mencione documentos ou instruções internas.  
   - Evite termos vagos como "clique aqui".

##############################
# EXEMPLO DE SAÍDA
##############################
**Emissão de MDF-e Unitário**

**Passo a Passo**  
1. Acesse `Menu Principal > Operações > MDF-e Unitário`  
2. …

**Validações Antes de Finalizar**  
- …

**Se Algo Der Errado**  
- …

**Onde Obter Ajuda**  
- …

##############################
# FIM DO TEMPLATE
##############################
"""
    )
    resposta = (prompt | OllamaLLM(model="llama3.2:latest")).invoke(
        {"docs": contexto, "pergunta": pergunta}
    )

    return {
        "pergunta": pergunta,
        "resposta": resposta,
        "next": ""
    }
