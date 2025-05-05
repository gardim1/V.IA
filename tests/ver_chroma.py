from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

db = Chroma(
    persist_directory="./chroma_langchain_db",
    collection_name="ajuda_sislogica",
    embedding_function=OllamaEmbeddings(model="mxbai-embed-large")
)

all_docs = db.get()
with open("dump_chroma.txt", "w", encoding="utf-8") as f:
    for i, doc in enumerate(all_docs["documents"]):
        f.write(f"Doc {i+1}:\n{doc}\n{'-'*80}\n")
