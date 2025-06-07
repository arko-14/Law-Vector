import os
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import re

# === Config ===
PINECONE_API_KEY = "pcsk_6kqUF1_LBEy7fbF4q6Ez6W4fPfYCBrb7eEZMDPzjYrJzCKuQnJkLZarXhHm5rnZKCaWGys"
PINECONE_ENV = "us-east-1"
INDEX_NAME = "lawvector"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"
DIMENSION = 384
BATCH_SIZE = 20  # Upsert vectors in batches of 100

# === Init Pinecone ===
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east1")
    )
index = pc.Index(INDEX_NAME)

# === Init Embedding ===
model = SentenceTransformer(EMBEDDING_MODEL)

# === Helpers ===
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)

def split_text(text, chunk_size=500, overlap=100):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i+chunk_size])
    return chunks

def sanitize_id(text_id):
    # Remove or replace any non-ASCII characters from ID to avoid Pinecone errors
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', text_id)

def vectors_exist_for_file(filename_prefix):
    dummy_vec = [0.0] * DIMENSION
    try:
        res = index.query(
            vector=dummy_vec,
            top_k=1,
            include_metadata=True,
            filter={"filename": {"$eq": filename_prefix}}
        )
        return len(res['matches']) > 0
    except Exception as e:
        print(f"Error checking vectors for file '{filename_prefix}': {e}")
        return False

# === Main Function ===
def build_vector_store(file_path=None, data_dir=None):
    if file_path and data_dir:
        raise ValueError("Provide either file_path or data_dir, not both.")
    if not file_path and not data_dir:
        raise ValueError("Provide either file_path or data_dir.")

    file_names = []
    if file_path:
        file_names = [file_path]
    elif data_dir:
        file_names = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.lower().endswith(".pdf")]

    for fname in file_names:
        base_fname = os.path.basename(fname)
        print(f"Checking if vectors for '{base_fname}' exist in Pinecone...")
        if vectors_exist_for_file(base_fname):
            print(f"Vectors for '{base_fname}' already exist. Skipping embedding.")
            continue

        print(f"Processing file: {base_fname}")

        text = extract_text_from_pdf(fname)
        chunks = split_text(text)

        batch = []
        for i, chunk in enumerate(chunks):
            vec = model.encode(chunk)
            vec_id = sanitize_id(f"{base_fname}_chunk_{i}")
            metadata = {"text": chunk, "filename": base_fname}
            batch.append((vec_id, vec.tolist(), metadata))

            if len(batch) >= BATCH_SIZE:
                index.upsert(vectors=batch)
                print(f"Upserted batch of {len(batch)} vectors for '{base_fname}'...")
                batch.clear()

        # Upsert any remaining vectors
        if batch:
            index.upsert(vectors=batch)
            print(f"Upserted final batch of {len(batch)} vectors for '{base_fname}'.")

    print("Build vector store completed.")

def get_context_from_query(query, k=4):
    query_vec = model.encode(query)
    res = index.query(vector=query_vec.tolist(), top_k=k, include_metadata=True)
    return [match['metadata']['text'] for match in res['matches']]

# === Example test run ===
if __name__ == "__main__":
    # Example: process just one uploaded document (no folder processing)
    build_vector_store(file_path="data/example.pdf")

    # Example query
    context = get_context_from_query("What is the purpose of this document?", k=3)
    for i, txt in enumerate(context):
        print(f"--- Context {i+1} ---\n{txt}\n")
