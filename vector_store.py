import os
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings

# === Hardcoded Pinecone & Embedding Config ===
PINECONE_API_KEY = "pcsk_6kqUF1_LBEy7fbF4q6Ez6W4fPfYCBrb7eEZMDPzjYrJzCKuQnJkLZarXhHm5rnZKCaWGys"
PINECONE_ENV      = "us-east-1"
INDEX_NAME        = "lawvector"
EMBEDDING_MODEL   = "sentence-transformers/paraphrase-MiniLM-L3-v2"
DIMENSION         = 384  # Embedding vector size for MiniLM-L3-v2

# Initialize Pinecone client
pc = Pinecone(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENV
)

# Ensure index exists
indexes = pc.list_indexes().names()
if INDEX_NAME not in indexes:
    # Set cloud and region based on your environment string
    # For "us-west1-gcp", cloud="gcp" and region="us-west1"
    spec = ServerlessSpec(
        cloud="gcp",
        region="us-west1"
    )
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=spec
    )

# Initialize Embedding Model
embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# === Functions ===
def build_vector_store(data_dir="data"):
    """
    Load up to 2 PDFs from `data_dir`, split into chunks, embed and upsert into Pinecone.
    """
    # 1. Load and split
    docs = []
    for fname in os.listdir(data_dir)[:2]:
        if not fname.lower().endswith(".pdf"): continue
        loader = PyPDFLoader(os.path.join(data_dir, fname))
        docs.extend(loader.load())

    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    if not chunks:
        print("No chunks to index.")
        return

    # 2. Prepare vectors for upsert
    to_upsert = []
    for i, chunk in enumerate(chunks):
        vec = embedding.embed_documents([chunk.page_content])[0]
        to_upsert.append((f"chunk_{i}", vec, {"text": chunk.page_content}))

    # 3. Upsert into Pinecone
    index = pc.Index(INDEX_NAME)
    index.upsert(vectors=to_upsert)
    print(f"Upserted {len(to_upsert)} chunks into Pinecone index '{INDEX_NAME}'.")


def get_context_from_query(query, k=4):
    """
    Embed `query`, query Pinecone for top `k` similar chunks, and return their text.
    """
    q_vec = embedding.embed_query(query)
    index = pc.Index(INDEX_NAME)
    resp = index.query(
        vector=q_vec,
        top_k=k,
        include_metadata=True
    )
    return [match['metadata']['text'] for match in resp['matches']]


if __name__ == "__main__":
    build_vector_store(data_dir="data")
    context = get_context_from_query("What is the purpose of this document?", k=3)
    for i, txt in enumerate(context):
        print(f"--- Context {i+1} ---")
        print(txt)
