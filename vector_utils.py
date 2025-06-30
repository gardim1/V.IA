from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import os
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-large")

def rerank_docs(query: str, docs: list, top_k: int = 10):
    pairs = [[query, doc.page_content] for doc in docs]
    scores = reranker.predict(pairs)
    scored = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored[:top_k]]


def get_embedding_function():
    return OllamaEmbeddings(model="mxbai-embed-large")


def get_retriever(filtro: str = None):
    embeddings = get_embedding_function()
    db_location = "./chroma_langchain_db"

    vector_store = Chroma(
        collection_name="ajuda_sislogica",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    search_kwargs = {"k": 20}
    if filtro:
        search_kwargs["filter"] = {"categoria": filtro}

    return vector_store.as_retriever(
        search_type="similarity", #mmr
        search_kwargs=search_kwargs
    )

def inferir_categoria(path: str) -> str:
    nome = os.path.basename(path).lower()

    if any(t in nome for t in ["cte", "mdf", "comprovante"]):
        return "CTE_MDFE"
    elif "roteirizacao" in nome or "rota" in nome:
        return "ROTEIRIZACAO"
    elif "relatorio" in nome:
        return "RELATORIOS"
    elif "devolucao" in nome or "recebimento" in nome:
        return "DEVOLUCAO"
    elif "chamado" in nome or "ocorrencia" in nome:
        return "CHAMADOS"
    elif "transportador" in nome:
        return "TRANSPORTADORA"
    elif "motorista" in nome or "veiculo" in nome:
        return "FROTA"
    elif "indenizacao" in nome:
        return "INDENIZACAO"
    else:
        return "GERAL"

def load_and_split_documents(file_paths):
    documentos = []

    for path in file_paths:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        categoria = inferir_categoria(path)
        sections = content.split("\n\n")

        for idx, sec in enumerate(sections):
            texto = sec.strip()
            if texto:
                documentos.append(
                    Document(
                        page_content=texto,
                        metadata={
                            "source": os.path.basename(path),
                            "section": idx,
                            "categoria": categoria,
                        },
                    )
                )

    # splitter = RecursiveCharacterTextSplitter(
    #     separators=[r"\n=====.*=====\n"], keep_separator=True
    # )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200
    )
    split_docs = splitter.split_documents(documentos)

    for i, doc in enumerate(split_docs):
        doc.metadata["id"] = f"{doc.metadata['source']}_{i}"

    return split_docs

def save_to_chroma(documents):
    embeddings = get_embedding_function()
    db_location = "./chroma_langchain_db"

    vector_store = Chroma(
        collection_name="ajuda_sislogica",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    existing_ids = set(vector_store.get()["ids"])
    novos_docs = [d for d in documents if d.metadata["id"] not in existing_ids]

    if novos_docs:
        vector_store.add_documents(
            documents=novos_docs,
            ids=[d.metadata["id"] for d in novos_docs],
        )

    return vector_store
