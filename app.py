import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import json

from vector_store import build_vector_store, get_context_from_query
from userupload import extract_text_from_pdf, summarize_text, prepare_prompt
from chatbot import call_perplexity_sonar

# ─── Load env & init app ─────────────────────────────────────────────
load_dotenv()
app = Flask(__name__)
CORS(app)

# ─── Supabase client ────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Build vector index on startup ──────────────────────────────────
build_vector_store(data_dir="data")

# ─── PDF Upload Route ───────────────────────────────────────────────
@app.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a PDF file under 'file'."}), 400

    save_path = os.path.join("data", file.filename)
    file.save(save_path)

    raw_text = extract_text_from_pdf(save_path)
    summary = summarize_text(raw_text)

    # ✅ Only re-index this single file, not all files
    build_vector_store(file_path=save_path)

    return jsonify({
        "message": f"Uploaded and indexed {file.filename}.",
        "summary": summary
    })

# ─── Contextual Chat Route ──────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json() or {}
    user_q = payload.get("query", "").strip()
    if not user_q:
        return jsonify({"error": "Field 'query' is required."}), 400

    chunks = get_context_from_query(user_q, k=4)
    if not chunks:
        return jsonify({"error": "No relevant documents found for your query."}), 404

    # ✅ No page_content, just raw strings now
    full_context = "\n---\n".join(chunks)

    summary = summarize_text(full_context)
    answer = call_perplexity_sonar(summary, user_q)

    return jsonify({"response": answer})

# ─── General Legal Advice Route ─────────────────────────────────────
@app.route("/general_advice", methods=["POST"])
def general_advice():
    payload = request.get_json() or {}
    user_q = payload.get("question", "").strip()
    if not user_q:
        return jsonify({"error": "Field 'question' is required."}), 400

    answer = call_perplexity_sonar(summary=None, user_query=user_q)

    try:
        res = supabase.table("legal_queries").insert({
            "query": user_q,
            "response": answer
        }).execute()
        app.logger.info(f"Inserted Q&A: {res.data}")
    except Exception as e:
        app.logger.error(f"Error storing to Supabase: {e}")

    return jsonify({"response": answer})

# ─── Opinion Map (graph generator) ─────────────────────────────────
@app.route("/opinion_map", methods=["POST"])
def opinion_map():
    payload = request.get_json() or {}
    case_summary = payload.get('summary', '').strip()
    if not case_summary:
        return jsonify({'error': 'Field summary is required.'}), 400

    prompt = (
        "Extract the main legal opinions and their relationships from the following summary. "
        "Return a JSON object with 'nodes': list of {id, label}, and 'edges': list of {source, target}. "
        f"Text: {case_summary}"
    )
    resp = call_perplexity_sonar(summary=None, user_query=prompt)
    app.logger.info(f"Perplexity response: {resp}")
    try:
        data = json.loads(resp)
        nodes = data.get('nodes', []) or []
        edges = data.get('edges', []) or []
        return jsonify({"nodes": nodes, "edges": edges})
    except Exception as parse_err:
        app.logger.error(f"Failed to parse Perplexity response: {parse_err}")
        return jsonify({
            'error': 'Failed to parse Perplexity response.',
            'raw_response': resp
        }), 500

# ─── Health Check ──────────────────────────────────────────────────
@app.route("/healthz")
def healthz():
    return jsonify(status="ok"), 200

# ─── Run App ───────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
