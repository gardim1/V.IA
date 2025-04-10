from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

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
