from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

import os

def get_retriever():
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    db_location = "./chroma_langchain_db"

    vector_store = Chroma(
        collection_name="ajuda_sislogica",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    return retriever

# 🔽 Adiciona isso aqui embaixo 🔽

def load_and_split_documents(file_paths):
    documents = []

    for path in file_paths:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            documents.append(Document(page_content=content, metadata={"source": os.path.basename(path)}))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )

    split_docs = splitter.split_documents(documents)
    return split_docs

def embed_documents(documents):
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    return embeddings.embed_documents([doc.page_content for doc in documents]), embeddings
