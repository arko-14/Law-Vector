import os
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-MiniLM-L3-v2"
EMBEDDING = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
INDEX_DIR = "faiss_index"

def build_vector_store(data_dir="data"):
    """Scan all PDFs in data_dir, split & embed into FAISS, and save locally."""
    docs = []
    for fname in os.listdir(data_dir):
        if fname.lower().endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(data_dir, fname))
            docs.extend(loader.load())
    if not docs:
        print("No PDF documents found in data directory!")
        return

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    if not chunks:
        print("No chunks created from documents!")
        return

    vs = FAISS.from_documents(chunks, EMBEDDING)
    vs.save_local(INDEX_DIR)
    print(f"Built FAISS index with {len(chunks)} chunks.")

def get_context_from_query(query, k=4):
    """Load FAISS index, run similarity search, and return the top-k chunks as context."""
    if not os.path.exists(INDEX_DIR):
        # Instead of returning a string, return an empty list
        return []

    try:
        vs = FAISS.load_local(INDEX_DIR, EMBEDDING, allow_dangerous_deserialization=True)
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return []

    try:
        hits = vs.similarity_search(query, k=k)
    except Exception as e:
        print(f"Error during similarity search: {e}")
        return []

    if not hits:
        print("No hits found for query.")
        return []

    return hits  # return list of Document objects
