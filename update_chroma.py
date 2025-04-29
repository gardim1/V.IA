import os
from vector_utils import load_and_split_documents, embed_documents
from langchain_chroma import Chroma

PASTA_BASE_TXT = "conteudos_novos_7"
CHROMA_PATH = "chroma_langchain_db"

def listar_txts(pasta):
    txt_files = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith('.txt')]
    print(f"Arquivos .txt encontrados na pasta {pasta}: {txt_files}")
    return txt_files

def validar_arquivo(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        conteudo = f.read()
        valido = len(conteudo.strip()) > 10
        print(f"Arquivo {caminho} {'é válido' if valido else 'não é válido'}.")
        return valido

def main():
    arquivos_validos = [f for f in listar_txts(PASTA_BASE_TXT) if validar_arquivo(f)]

    if not arquivos_validos:
        print("Nenhum arquivo válido encontrado.")
        return
    
    print(f"Arquivos válidos encontrados: {arquivos_validos}")

    docs = load_and_split_documents(arquivos_validos)
    print(f"{len(docs)} documentos carregados e divididos.")

    _, embeddings = embed_documents(docs) 

    db = Chroma(
        persist_directory=CHROMA_PATH,
        collection_name="ajuda_sislogica",
        embedding_function=embeddings
    )

    db.add_documents(docs)
    print("ChromaDB atualizado com sucesso!")
    print("Documentos no banco após update:")
    print(db._collection.count())


if __name__ == "__main__":
    main()
