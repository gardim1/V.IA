from langchain.vectorstores import Chroma

db = Chroma(persist_directory="chroma_langchain_db", collection_name="ajuda_sislogica")


# doc_id = "id_do_documento"  

# db._collection.delete([doc_id]) 
# print(f"Documento {doc_id} removido com sucesso.")


for doc in db._collection.peek():  
    print(doc)
