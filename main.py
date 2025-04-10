from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever

model = Ollama(model="llama3.2")

template = """
Você é uma IA especialista no sistema TMS da empresa Sislogica. Você deve repsonder todas as perguntas do usuário de forma completa, clara e profissional. Se a pergunta não existir no banco vetorial diga explicitamente que você não sabe e oriente o cliente a procurar ajuda com o time de suporte. Você DEVE responder tudo em portgues brasileiro.

Aqui estao os documentos do banco vetorial: {dados}

Aqui está a pergunta para responder: {pergunta}
"""

prompt = ChatPromptTemplate.from_template(template)

chain = prompt | model

while True:
    print("\n\n----------------------------")
    pergunta = input("Faça sua pergunta (q para sair): ")
    print("\n\n")
    if pergunta == "q":
        break

    dados = retriever.invoke(pergunta)
    resultado = chain.invoke({"dados": dados,"pergunta": pergunta})
    print(resultado)


#excluir banco vetorial rm -r chroma_langchain_db/