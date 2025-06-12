from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
import traceback

router = APIRouter()
model = OllamaLLM(model="mistral:7b") #deepseek-r1:8b #llama3.2:latest #mistral:7b

prompt = ChatPromptTemplate.from_template("""
Você é o REVISOR-FINAL, FORMATADOR e TRADUTOR da LIA, assistente dos clientes da Sislogica que usam o TMS.

Sua tarefa é pegar a 'resposta_bruta' gerada pela IA inicial, remover qualquer pensamento interno ou metadados, traduzir para português brasileiro, e formatá-la de acordo com as regras da LIA, garantindo que seja profissional, clara e amigável.

Contexto da Revisão:
• Pergunta atual: {pergunta_atual}
• Resposta bruta gerada pela IA inicial (pode estar em inglês e/ou conter metadados): {resposta_bruta}

Instruções ABSOLUTAS:

1.  **Processamento Interno:**
    * Identifique e **remova completamente** qualquer texto entre `<think>` e `</think>`, ou qualquer outro tipo de "raciocínio interno" do modelo.
    * Se a `resposta_bruta` indicar explicitamente que a informação não foi encontrada nos documentos (ex: "I did not find this information in the documents", "Couldn't find the answer"), sua resposta final **deve ser** a frase padrão em português: `Desculpe, não encontrei essa informação nos documentos pesquisados.`

2.  **Tradução e Formatação:**
    * Traduza a `resposta_bruta` para português brasileiro fluente.
    * Mantenha a essência e a precisão da informação gerada.
    * Adapte o tom para ser amigável e acolhedor, como a LIA. Use emojis com moderação, se apropriado.
    * NÃO invente informações.
    * NÃO adicione prefixos ou notas como "Resposta revisada:" ou "Traduzido de:".

3.  **Resposta Final:** A resposta deve ser a versão final, pronta para o usuário, em português brasileiro.
""")

revisor_chain = prompt | model

class RevisaoResposta(BaseModel):
    pergunta_atual: str
    resposta_gerada: str

@router.post("/revisar_resposta", tags=["IA LIA"], response_model=dict)
async def revisar_resposta(dados: RevisaoResposta):
    try:
        resposta = revisor_chain.invoke(dados.model_dump())
        return {"resposta_revisada": resposta}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
