import os
import re
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document


def get_embedding_function():
    return HuggingFaceEmbeddings(model_name="intfloat/e5-large-v2")


def load_and_split_documents(file_paths):
    documents = []

    for path in file_paths:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

            partes = re.split(r"(=====.*?=====)", content)

            for i in range(1, len(partes), 2):
                titulo = partes[i].strip()
                corpo = partes[i + 1].strip() if i + 1 < len(partes) else ""

                if len(corpo) > 30:
                    texto_final = f"passage: {titulo}\n{corpo}"
                    doc = Document(
                        page_content=texto_final,
                        metadata={
                            "source": os.path.basename(path),
                            "titulo": titulo.replace("=", "").strip(),
                            "id": f"{os.path.basename(path)}_{i}"
                        }
                    )
                    documents.append(doc)

    print(f"{len(documents)} documentos parseados com sucesso.")
    return documents

def save_to_chroma(documents):
    embeddings = get_embedding_function()
    db_location = "./chroma_langchain_db"

    vector_store = Chroma(
        collection_name="ajuda_sislogica",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    existing_ids = set(vector_store.get()["ids"])
    new_docs = [doc for doc in documents if doc.metadata["id"] not in existing_ids]
    new_ids = [doc.metadata["id"] for doc in new_docs]

    if new_docs:
        vector_store.add_documents(documents=new_docs, ids=new_ids)
        vector_store.persist()
        print(f"{len(new_docs)} novos documentos adicionados.")
    else:
        print("Nenhum documento novo para adicionar.")

    return vector_store

def get_retriever():
    embeddings = get_embedding_function()
    db_location = "./chroma_langchain_db"

    vector_store = Chroma(
        collection_name="ajuda_sislogica",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )
    return retriever
