import os
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Use lighter, memory-efficient embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-MiniLM-L3-v2"
EMBEDDING = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

# Remove reliance on prebuilt index directory
INDEX = None

def build_vector_store(data_dir="data"):
    """Scan all PDFs in data_dir, split & embed into FAISS (in-memory)."""
    docs = []
    for fname in os.listdir(data_dir):
        if fname.lower().endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(data_dir, fname))
            docs.extend(loader.load())
    if not docs:
        print("No PDF documents found in data directory!")
        return None

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    if not chunks:
        print("No chunks created from documents!")
        return None

    print(f"Built FAISS index with {len(chunks)} chunks.")
    return FAISS.from_documents(chunks, EMBEDDING)

def get_context_from_query(query, vector_store, k=4):
    """Run similarity search on in-memory FAISS store and return top-k results."""
    if not vector_store:
        print("No vector store initialized.")
        return []

    try:
        hits = vector_store.similarity_search(query, k=k)
    except Exception as e:
        print(f"Error during similarity search: {e}")
        return []

    if not hits:
        print("No hits found for query.")
        return []

    return hits


    if not hits:
        print("No hits found for query.")
        return []

    return hits
