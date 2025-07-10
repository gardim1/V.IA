from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_utils import get_retriever
from vector_utils import get_retriever, rerank_docs

from utils.history_chain import wrap_with_history

def relatorios_agent(state: dict) -> dict:
    pergunta = state["pergunta"]
    user_id = state.get("user_id")  
    if not user_id:
        raise ValueError("user_id está ausente ou é None")

    retriever = get_retriever(filtro="RELATORIOS")
    docs = retriever.invoke(pergunta)
    docs = rerank_docs(pergunta, docs, top_k=3)
    contexto = "\n".join(d.page_content for d in docs) if docs else ""

    print("\n=== [RELATORIOS] Chunks recuperados individualmente ===")
    for i, d in enumerate(docs, 1):
        print(f"Doc {i}:\n{d.page_content}\n")

    contexto = "\n".join(d.page_content for d in docs)

    print("\n=== [RELATORIOS] Texto total passado para IA ===")
    print(contexto)
    print("===================================================\n")

    prompt = ChatPromptTemplate.from_template(
    """
##############################
# CONTEXTO INTERNO — NÃO MOSTRAR AO USUÁRIO
##############################
Você é a **LIA** (Logistics Intelligence Assistant) especialista na categoria relatorios.
Responda **exclusivamente** com base nos DOCUMENTOS DE REFERÊNCIA abaixo.

##############################
# DOCUMENTOS DE REFERÊNCIA
##############################
{docs}

##############################
# PERGUNTA DO USUÁRIO
##############################
{pergunta}

### RESUMO DA CONVERSA(CASO PRECISE LEMBRAR DE ALGUMA INFORMAÇÃO, COMO O NOME DO USUÁRIO, A EMPRESA OU OUTRAS INFORMAÇÕES RELEVANTES):
{resumo_usuario}

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
    pipeline = prompt | OllamaLLM(model="mistral:7b")
    chain = wrap_with_history(pipeline, user_id)

    resposta = chain.invoke(
        {"docs": contexto, "pergunta": pergunta},
        config={"configurable": {"session_id": user_id}}
    )

    return {
        "pergunta": pergunta,
        "resposta": resposta,
        "next": "",
        "user_id": user_id
    }
