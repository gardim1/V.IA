from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import textwrap

def update_chroma_from_folder(folder_path):
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    db_location = "./chroma_langchain_db"
    vector_store = Chroma(
        collection_name="ajuda_sislogica",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    existing_ids = set(vector_store.get()["ids"])
    documents = []
    ids = []

    for file in os.listdir(folder_path):
        if file.endswith(".txt"):
            with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
                content = f.read()
                chunks = textwrap.wrap(content, width=1000, break_long_words=False, drop_whitespace=True)
                for i, chunk in enumerate(chunks):
                    doc_id = f"{file}_{i}"
                    if doc_id not in existing_ids:
                        documents.append(Document(page_content=chunk, metadata={"source": file}, id=doc_id))
                        ids.append(doc_id)

    if documents:
        vector_store.add_documents(documents=documents, ids=ids)
        vector_store.persist()

    return vector_store

vector_store = update_chroma_from_folder("conteudos")

retriever = vector_store.as_retriever(search_kwargs={"k": 5})
