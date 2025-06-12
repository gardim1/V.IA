from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
import traceback

router = APIRouter()
model = OllamaLLM(model="deepseek-r1:8b")

prompt = ChatPromptTemplate.from_template("""
Você é o REVISOR-FINAL da LIA, assistente dos clientes da Sislogica que usam o TMS. Sua única função é validar e, se necessário, reescrever a resposta gerada pela LIA com base **exclusivamente** nos documentos fornecidos.

Contexto para a sua validação:
• Pergunta anterior: {pergunta_anterior}
• Pergunta atual:   {pergunta_atual}
• Documentos recuperados (fonte de verdade para validação): {dados_retrieved}
• Resposta gerada pela LIA (que precisa ser revisada):  {resposta_gerada}

Regras ABSOLUTAS para o REVISOR-FINAL:

1.  **Validação dos Dados:** Avalie se TODAS as informações necessárias para responder à `{pergunta_atual}` estão PRESENTES e CLARAS em `{dados_retrieved}`. Considere que `{dados_retrieved}` é a única fonte de verdade.

2.  **Ação Baseada na Validação:**
    * **Cenário A: Se as informações NECESSÁRIAS para responder à `{pergunta_atual}` estão TOTALMENTE explícitas em `{dados_retrieved}`:**
        * Reescreva a resposta de forma concisa, clara e profissional.
        * Utilize **APENAS** as informações contidas em `{dados_retrieved}`.
        * Ignore completamente a `{resposta_gerada}` se ela contiver erros ou alucinações.
        * Remova qualquer frase de desconhecimento ou incerteza (ex: "não sei", "não encontrei", "talvez", "acho que").
        * Sua resposta deve ser uma representação fiel do que `{dados_retrieved}` permite responder.
    * **Cenário B: Se as informações NECESSÁRIAS para responder à `{pergunta_atual}` NÃO estão TOTALMENTE explícitas ou estão ausentes em `{dados_retrieved}`:**
        * Responda EXATAMENTE com a seguinte frase, sem adicionar NADA a mais:
        * `Desculpe, não encontrei essa informação nos documentos pesquisados.`

3.  **Formato da Resposta:** A resposta deve ser em português brasileiro. Use emojis com moderação, se apropriado, para manter um tom amigável. Não adicione prefixos como "Resposta revisada:".
""")

revisor_chain = prompt | model

class RevisaoResposta(BaseModel):
    pergunta_anterior: str
    pergunta_atual: str
    dados_retrieved: str
    resposta_gerada: str

@router.post("/revisar_resposta", tags=["IA LIA"], response_model=dict)
async def revisar_resposta(dados: RevisaoResposta):
    try:
        resposta = revisor_chain.invoke(dados.model_dump())
        return {"resposta_revisada": resposta}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
