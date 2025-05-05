from vector_utils import get_retriever

retriever = get_retriever()
docs = retriever.invoke("Como cadastrar motoristas?")

print("\n=== DOCUMENTOS RETORNADOS ===\n")
for i, doc in enumerate(docs):
    print(f"Doc {i+1}:")
    print(f"Page Content: {doc.page_content}")
    print(f"Metadata: {doc.metadata}")
    print("\n")
    print("===" * 35)
print("\n=== FIM DOS DOCUMENTOS ===\n")