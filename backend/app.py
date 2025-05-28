# app.py
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import json
import networkx as nx
import matplotlib.pyplot as plt

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
# ─── Route: Generate Opinion Map ───────────────────────────────
@app.route("/opinion_map", methods=["POST"])
def opinion_map():
    payload = request.get_json() or {}
    case_summary = payload.get('summary', '').strip()
    if not case_summary:
        return jsonify({'error': 'Field summary is required.'}), 400

    # Ask Perplexity for key opinions and relationships
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
    except Exception as parse_err:
        app.logger.error(f"Failed to parse Perplexity response as JSON: {parse_err}")
        return jsonify({
            'error': 'Failed to parse Perplexity response as JSON.',
            'raw_response': resp
        }), 500
@app.route("/healthz")
def healthz():
    return jsonify(status="ok"), 200

    # Build graph
    G = nx.DiGraph()
    if not nodes:
        # Fallback: single node for entire summary
        G.add_node(0, label='Main Opinion')
    else:
        for n in nodes:
            G.add_node(n.get('id', ''), label=n.get('label', ''))
    if edges:
        for e in edges:
            G.add_edge(e.get('source'), e.get('target'))

    # Draw and save
    fig, ax = plt.subplots(figsize=(8,6))
    pos = nx.spring_layout(G) if G.nodes else {n: (0,0) for n in G.nodes}
    nx.draw(G, pos, with_labels=True, labels=nx.get_node_attributes(G,'label'), ax=ax)
    img_path = os.path.join('data', 'opinion_map.png')
    fig.savefig(img_path)
    plt.close(fig)

    return send_file(img_path, mimetype='image/png')

# ─── Run the app ────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
