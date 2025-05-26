# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client

from vector_store import build_vector_store, get_context_from_query
from userupload import extract_text_from_pdf, summarize_text, prepare_prompt
from chatbot import call_perplexity_sonar

# ─── Load env (for other configs) & init app & CORS ────────────────
load_dotenv()
app = Flask(__name__)
CORS(app)

# ─── Supabase client setup (hardcoded) ─────────────────────────────
SUPABASE_URL = "https://ctrbrlsgdteajwncawzu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN0cmJybHNnZHRlYWp3bmNhd3p1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njc4NDAyOSwiZXhwIjoyMDYyMzYwMDI5fQ.3yIi76DPD0uEjobuwFS8C90YxhfcnK8lcbRMDHdsFls"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Build FAISS index on startup ────────────────────────────────
build_vector_store(data_dir="data")

# ─── PDF Upload Route ───────────────────────────────────────────
@app.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a PDF file under 'file'."}), 400

    save_path = os.path.join("data", file.filename)
    file.save(save_path)

    raw_text = extract_text_from_pdf(save_path)
    summary = summarize_text(raw_text)
    build_vector_store(data_dir="data")

    return jsonify({
        "message": f"Uploaded and indexed {file.filename}.",
        "summary": summary
    })

# ─── Contextual Chat Route ───────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json() or {}
    user_q = payload.get("query", "").strip()
    if not user_q:
        return jsonify({"error": "Field 'query' is required."}), 400

    chunks = get_context_from_query(user_q, k=4)
    if not chunks:
        return jsonify({"error": "No relevant documents found for your query."}), 404

    full_context = "\n---\n".join(
        c.page_content if hasattr(c, "page_content") else str(c)
        for c in chunks
    )
    summary = summarize_text(full_context)
    answer = call_perplexity_sonar(summary, user_q)

    return jsonify({"response": answer})

# ─── General Advice Route ────────────────────────────────────────
@app.route("/general_advice", methods=["POST"])
def general_advice():
    payload = request.get_json() or {}
    user_q = payload.get("question", "").strip()
    if not user_q:
        return jsonify({"error": "Field 'question' is required."}), 400

    # 1) Get answer from Perplexity
    answer = call_perplexity_sonar(summary=None, user_query=user_q)

    # 2) Insert into Supabase
    try:
        res = supabase.table("legal_queries").insert({
            "query": user_q,
            "response": answer
        }).execute()
        app.logger.info(f"Inserted Q&A: {res.data}")
    except Exception as e:
        app.logger.error(f"Error storing to Supabase: {e}")

    # 3) Return the answer
    return jsonify({"response": answer})

# ─── Run the app ────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
