from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
import re

prompt = PromptTemplate.from_template("""
Classifique a pergunta abaixo em UMA das categorias:
CTE_MDFE, ROTEIRIZACAO, RELATORIOS, DEVOLUCAO,
CHAMADOS, TRANSPORTADORA, FROTA, INDENIZACAO, GERAL.
                                      
Se a pergunta for algo trivial ou de cortesia, classifique como SMALL_TALK.
                                      
CHAMADOS:
    - CADASTRO DE OCORRÊNCIA SISTEMA
    - CADASTRO DE USUÁRIO

CTE_MDFE:
    - CHAVE CTE ANTERIOR NÃO INFORMADA
    - CORREÇÃO CTE ANTERIOR CANCELADO
    - ENTREGA MDF-E UNITÁRIO
    - ERRO DE VALOR DO ICMS
    - EVENTO JÁ REGISTRADO NA SEFAZ
    - INSCRIÇÃO ESTADUAL DESTINATÁRIO NÃO INFORMADA
    - INSCRIÇÃO ESTADUAL REMETENTE NÃO INFORMADA
    - MDF-E UNITÁRIO
    - NFE COM MAIS DE 6 MESES
    - RELATÓRIO UPLOAD COMPROVANTE CTE

DEVOLUCAO:
    - CADASTRO DE CLIENTE SERVIÇO
    - CADASTRO DE SERVIÇO
    - RECEBIMENTO TRANSFERÊNCIA COM FALTANTES

FROTA:
    - CADASTRO DE CONFIGURAÇÃO DE VEÍCULO
    - CARGAS CANCELADAS
    - DASHBOARD CARGA MOTORISTA
    - FECHAMENTO POR PERÍODO
    - MAPA MONITORAMENTO CARGAS
    - MONITORAMENTO PAINEL PERFORMANCE
    - QRCODE APP
    - SALDO DOS MOTORISTAS

GERAL:
    - CADASTRO DE CLIENTE SERVIÇO
    - CADASTRO DE FILIAL GRUPO EMPRESARIAL
    - CADASTRO DE GRUPO
    - CADASTRO DE MODELO
    - CADASTRO DE ROTA TRANSFERÊNCIA
    - CADASTRO DE SEGUROS
    - CADASTRO DE USUÁRIO
    - ERRO DE VALOR DO ICMS
    - INSTALAÇÃO DO CONECTOR

INDENIZACAO:
    - CADASTRO DE CATEG. PRODUTO
    - CADASTRO DE FAROL
    - CADASTRO DE MOTIVO
    - CADASTRO DE RESPONSABILIDADE
    - CADASTRO DE STATUS
    - CADASTRO DE STATUS ROTEIRO

RELATORIOS:
    - ERROS DE IMPORTACAO
    - RELATÓRIO CARREGAMENTO
    - RELATÓRIO CONSULTA DE REMESSA RÁPIDA
    - RELATÓRIO CONSULTA DE REMESSA SIMPLIFICADA
    - RELATÓRIO CORREÇÃO DE CTE
    - RELATÓRIO CTE
    - RELATÓRIO FINANCEIRO REMESSA
    - RELATÓRIO LANÇAMENTOS CUSTOS
    - RELATÓRIO NFSE
    - RELATÓRIO OCORRÊNCIA EM LOTE
    - RELATÓRIO REENVIO DE OCORRÊNCIA

ROTEIRIZACAO:
    - CADASTRO DE PERCURSO
    - CADASTRO DE ROTA ENTREGA ABRANGÊNCIA  
    - CADASTRO DE ROTA TRANSFERÊNCIA
    - ENTREGA SHOPEE INTERMEDIÁRIO
    - LANÇAMENTO ROTAS MERCADO LIVRE
    - MAPA MONITORAMENTO CARGAS
    - MONITORAMENTO DE ROTAS
    - PEDIDOS SHOPEE LM
    - ROTEIRIZAÇÃO COM FILTROS
    - TRANSFERÊNCIA LOTE
    - À ROTEIRIZAR

TRANSPORTADORA:
    - CADASTRO DE FILIAL TRANSPORTADOR.
    - CADASTRO DE TRANSPORTADOR
    - CADASTRO DE TRANSPORTADOR PREÇO FRETE
    - CADASTRO DE TRANSPORTADOR SERVIÇO
    - CADASTRO DE TRANSPORTADOR TABELA PREÇO
    - CADASTRO DE TRANSPORTADOR TABELA REGIÃO CEP
    - VERIFICAR CEP TRANSPORTADOR                                     

Responda APENAS com o nome exato da categoria, sem explicações.

Pergunta: {pergunta}
Categoria:
""")

model = OllamaLLM(model="llama3:8b")
chain = prompt | model

SMALL_TALK_PATTERNS = re.compile(
    r"^(oi|olá|ola|e[ai]\b|bom dia|boa tarde|boa noite|"
    r"tudo bem\??|como você está\??|qual.*seu nome|quem.*você|obrigado|obrigada)",
    re.I
)

def roteador_tool(state: dict) -> dict:
    pergunta = state["pergunta"].strip()
    user_id = state.get("user_id")

    if SMALL_TALK_PATTERNS.match(pergunta):
        categoria = "SMALL_TALK"
    else:
        categoria = chain.invoke({"pergunta": pergunta}).strip().upper()

    validas = {
        "SMALL_TALK",
        "CTE_MDFE", "ROTEIRIZACAO", "RELATORIOS", "DEVOLUCAO",
        "CHAMADOS", "TRANSPORTADORA", "FROTA", "INDENIZACAO", "GERAL"
    }
    if categoria not in validas:
        categoria = "GERAL"

    return {
        "pergunta": pergunta,
        "resposta": "",
        "next": categoria.lower(),
        "user_id": user_id
    }
