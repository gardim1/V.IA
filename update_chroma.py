import os
from vector_utils import load_and_split_documents, save_to_chroma

PASTA_BASE_TXT = "cconteudos_novos_8"
CHROMA_PATH = "chroma_langchain_db"

def listar_txts(pasta: str):
    return [
        os.path.join(pasta, f)
        for f in os.listdir(pasta)
        if f.endswith(".txt")
    ]

def validar_arquivo(caminho: str) -> bool:
    with open(caminho, "r", encoding="utf-8") as f:
        return len(f.read().strip()) > 10

def main():
    txts_validos = [
        p for p in listar_txts(PASTA_BASE_TXT) if validar_arquivo(p)
    ]

    if not txts_validos:
        print("Nenhum .txt válido encontrado.")
        return

    print(f"{len(txts_validos)} arquivos válidos → carregando…")
    docs = load_and_split_documents(txts_validos)
    print(f"{len(docs)} chunks gerados → enviando ao ChromaDB…")

    save_to_chroma(docs)
    print("✅ Base vetorial atualizada com sucesso!")

if __name__ == "__main__":
    main()
