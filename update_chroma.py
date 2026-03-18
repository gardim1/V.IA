import os
import shutil

from vector_utils import CHROMA_PATH, get_vector_store, load_and_split_documents, save_to_chroma

PASTA_BASE_TXT = "conteudos_vini_02"


def listar_txts(pasta: str):
    if not os.path.isdir(pasta):
        print(f"Pasta de documentos nao encontrada: {pasta}")
        return []

    return [
        os.path.join(pasta, file_name)
        for file_name in os.listdir(pasta)
        if file_name.endswith(".txt")
    ]


def validar_arquivo(caminho: str) -> bool:
    with open(caminho, "r", encoding="utf-8") as file_pointer:
        return len(file_pointer.read().strip()) > 10


def main():
    txts_validos = [path for path in listar_txts(PASTA_BASE_TXT) if validar_arquivo(path)]

    if not txts_validos:
        print("Nenhum .txt valido encontrado. Mantendo o backend no ar sem reconstruir a base.")
        return

    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        print(f"Base anterior removida: {CHROMA_PATH}")

    get_vector_store.cache_clear()

    print(f"{len(txts_validos)} arquivos validos -> carregando...")
    docs = load_and_split_documents(txts_validos)
    print(f"{len(docs)} chunks gerados -> enviando ao ChromaDB...")

    save_to_chroma(docs)
    print("Base vetorial atualizada com sucesso!")


if __name__ == "__main__":
    main()
