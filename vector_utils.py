from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from llm_provider import get_embed_model

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_langchain_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "perfil_vinicius")


@dataclass
class RetrievedDocument:
    document: Document
    score: float | None = None


@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    return Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=CHROMA_PATH,
        embedding_function=get_embed_model(),
    )


def get_retriever(filtro: str | None = None, k: int = 6):
    search_kwargs = {"k": k}
    if filtro:
        search_kwargs["filter"] = {"categoria": filtro}
    return get_vector_store().as_retriever(search_type="similarity", search_kwargs=search_kwargs)


def search_documents(query: str, limit: int = 6, filtro: str | None = None) -> list[RetrievedDocument]:
    results = get_vector_store().similarity_search_with_score(
        query,
        k=limit,
        filter={"categoria": filtro} if filtro else None,
    )
    return [RetrievedDocument(document=doc, score=score) for doc, score in results]


def get_vector_store_health() -> dict:
    try:
        vector_store = get_vector_store()
        payload = vector_store.get()
        return {
            "provider": "chroma",
            "status": "ok",
            "collection_name": CHROMA_COLLECTION_NAME,
            "persist_directory": CHROMA_PATH,
            "document_count": len(payload.get("ids", [])),
        }
    except Exception as exc:  # pragma: no cover - depends on local storage
        return {
            "provider": "chroma",
            "status": "error",
            "collection_name": CHROMA_COLLECTION_NAME,
            "persist_directory": CHROMA_PATH,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _content_has_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _inferir_categoria_por_conteudo(content: str) -> str | None:
    normalized = content.lower()

    if "pergunta frequente:" not in normalized:
        return None

    faq_question = normalized.split("pergunta frequente:", 1)[1].splitlines()[0].strip()
    if not faq_question:
        return None

    if _content_has_any(faq_question, ("formacao", "faculdade", "curso", "fiap", "estuda")):
        return "FORMACAO"
    if _content_has_any(faq_question, ("idade", "quantos anos", "fale sobre", "quem e", "quem eh")):
        return "IDENTIDADE"
    if _content_has_any(
        faq_question,
        ("experiencia", "experiencias", "carreira", "emprego", "trabalhou", "ultimo emprego"),
    ):
        return "CARREIRA"
    if _content_has_any(faq_question, ("projeto", "projetos", "desafio tecnico")):
        return "PROJETOS"
    if _content_has_any(faq_question, ("5 anos", "futuro", "objetivo", "trabalhar nesta empresa")):
        return "OBJETIVOS"
    if _content_has_any(faq_question, ("equipe", "pressao", "pontos fortes", "pontos de melhoria", "contratar")):
        return "HABILIDADES"

    return "IDENTIDADE"


def inferir_categoria(path: str, content: str | None = None) -> str:
    nome = os.path.basename(path).lower()

    if "identidade" in nome:
        return "IDENTIDADE"
    if "faq" in nome or "recrutador" in nome:
        return _inferir_categoria_por_conteudo(content or "") or "IDENTIDADE"
    if "vida_pessoal" in nome or "pessoal" in nome:
        return "VIDA_PESSOAL"
    if "relacionamento" in nome or "namorada" in nome:
        return "RELACIONAMENTOS"
    if "formacao" in nome or "faculdade" in nome or "estudos" in nome:
        return "FORMACAO"
    if "carreira" in nome or "profissao" in nome or "trabalho" in nome:
        return "CARREIRA"
    if "projeto" in nome or "portfolio" in nome:
        return "PROJETOS"
    if "habilidade" in nome or "stack" in nome or "tecnologia" in nome or "diferencia" in nome or "problema" in nome:
        return "HABILIDADES"
    if "objetivo" in nome or "meta" in nome or "planos" in nome:
        return "OBJETIVOS"
    if "preferencia" in nome or "estilo" in nome or "forma_de_pensar" in nome:
        return "PREFERENCIAS"
    return "IDENTIDADE"


def load_and_split_documents(file_paths: list[str]) -> list[Document]:
    documentos: list[Document] = []

    for path in file_paths:
        with open(path, "r", encoding="utf-8") as file_pointer:
            content = file_pointer.read()

        secoes = content.split("=====")

        for secao in secoes:
            secao = secao.strip()
            if not secao:
                continue

            categoria = inferir_categoria(path, secao)

            documentos.append(
                Document(
                    page_content=secao,
                    metadata={
                        "source": os.path.basename(path),
                        "categoria": categoria,
                    },
                )
            )

    splitter = RecursiveCharacterTextSplitter(
        separators=["\n=====", "\n\n", "\n", " "],
        chunk_size=500,
        chunk_overlap=100,
        keep_separator=True,
    )

    split_docs = splitter.split_documents(documentos)
    for index, doc in enumerate(split_docs):
        doc.metadata["id"] = f"{doc.metadata['source']}_{index}"

    return split_docs


def save_to_chroma(documents: list[Document]) -> Chroma:
    vector_store = get_vector_store()
    existing = vector_store.get()
    existing_ids = set(existing["ids"]) if existing and existing.get("ids") else set()
    novos_docs = [doc for doc in documents if doc.metadata["id"] not in existing_ids]

    if novos_docs:
        vector_store.add_documents(
            documents=novos_docs,
            ids=[doc.metadata["id"] for doc in novos_docs],
        )

    return vector_store
