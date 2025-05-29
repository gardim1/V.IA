import re
from langchain.docstore.document import Document
import os

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
                    doc = Document(
                        page_content=f"{titulo}\n{corpo}",
                        metadata={
                            "source": os.path.basename(path),
                            "titulo": titulo.replace("=", "").strip(),
                            "id": f"{os.path.basename(path)}_{i}"
                        }
                    )
                    documents.append(doc)

    print(f"{len(documents)} documentos parseados com sucesso.")

    # Agora salva tudo num novo arquivo
    with open("documento_parseado.txt", "w", encoding="utf-8") as f:
        for doc in documents:
            f.write(f"{doc.page_content}\n\n")
            f.write("========== FIM DO BLOCO ==========\n\n")

    print("Arquivo 'documento_parseado.txt' criado com sucesso.")

    return documents

# Executar o parser e salvar o arquivo
load_and_split_documents(["conteudos_novos_7/resultado_com_caminhos_final.txt"])
