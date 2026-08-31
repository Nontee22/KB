vector_store = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=30,
    chunk_overlap=5,
    separators=["。", "，", " "]
)
vector_store.similarity_search(query, k=2)