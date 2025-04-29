from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_text_splitters import CharacterTextSplitter
import os

def get_retriever():
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    db_location = "./chroma_langchain_db"

    vector_store = Chroma(
        collection_name="ajuda_sislogica",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 10}
)
    return retriever

def load_and_split_documents(file_paths):
    documents = []

    for path in file_paths:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

            
            sections = content.split('\n\n')
            for idx, section in enumerate(sections):
                section = section.strip()
                if section:
                    documents.append(Document(
                        page_content=section,
                        metadata={
                            "source": os.path.basename(path),
                            "section": idx  
                        }
                    ))

    splitter = RecursiveCharacterTextSplitter(
        separators=[r"\n=====.*=====\n"],
        keep_separator=True,
    )

    split_docs = splitter.split_documents(documents)

    for i, doc in enumerate(split_docs):
        doc.metadata["id"] = f"{doc.metadata['source']}_{i}"

    return split_docs

def embed_documents(documents):
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    return embeddings.embed_documents([doc.page_content for doc in documents]), embeddings

def save_to_chroma(documents):
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
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

    return vector_store
