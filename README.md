# 🧠 Law Vector 

A powerful, AI-driven legal document search and understanding tool built for lawyers, law students, and legal researchers. This system leverages vector embeddings and FAISS (Facebook AI Similarity Search) to help users find, compare, and understand legal cases with ease and accuracy.

---

## 🔍 Overview

Legal research is time-consuming, and traditional keyword-based search often fails to grasp the deeper meaning behind legal cases. **Law Vector** changes that by using natural language understanding and semantic search to find the most relevant case law documents.

With a user-friendly interface and robust backend, you can:

* Upload your own legal documents.
* Query about laws or legal cases using natural language.
* Receive highly relevant answers and similar legal references from indexed documents.

---

## 📁 Project Structure

```
backend/
│
├── __pycache__/            # Compiled Python cache files
├── data/                   # Folder for raw or uploaded legal data
├── faiss_index/            # Stores FAISS vector index files
├── index.faiss/            # Another possible vector storage location
├── law_index/              # Directory for law-specific indexed content
│
├── .env                    # Environment variables (e.g., API keys, DB URI)
├── app.py                  # Main entry point to run the backend application (FastAPI/Flask)
├── chatbot.py              # Core logic for handling chat and user queries
├── law_index.faiss         # Serialized FAISS index file
├── userupload.py           # Handles file uploads and document parsing
├── vector_store.py         # Manages embeddings and vector database operations
│
├── frontend.py             # Command-line or minimal GUI for user interaction
├── LICENSE                 # Open source license
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
```

---

## ⚙️ Key Components Explained

### 🔹 `app.py`

This is the backend server script. It defines routes (probably using FastAPI or Flask) for user interaction such as:

* File upload
* Submitting a query
* Receiving answers

### 🔹 `chatbot.py`

Implements the chatbot interface that:

* Accepts user questions in natural language
* Uses embeddings and FAISS to retrieve relevant legal texts
* Returns a summarized or direct response to the user

### 🔹 `userupload.py`

Manages the upload process:

* Accepts legal PDFs or text files
* Converts them into chunks for vector embedding
* Stores them for indexing

### 🔹 `vector_store.py`

Handles:

* Generating text embeddings (e.g., via OpenAI, HuggingFace models)
* Managing vector indexing using FAISS
* Searching vectors semantically

### 🔹 `law_index.faiss`

A saved FAISS index that allows fast vector-based searching. This is built on your legal corpus.

---

## 📦 Installation

### 🔧 Requirements

* flask 
* flask-cors
* python-dotenv
* requests
* langchain
* faiss-cpu 
* sentence-transformers 
* pypdf 
* pdfplumber
* supabase
* transformers

### 🛠️ Setup

```bash
git clone https://github.com/arko-14/law-vector.git
cd law-vector
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 🔐 Environment Setup

Create a `.env` file and include any keys or configurations (Perplexity api)

```
PERPLEXITY_API_KEY=your-secret-api-key
PERPLEXITY_API_URL=https://api.perplexity.ai/query

```

---

## 🚀 Usage

### Start the Backend Server

```bash
python app.py
```

### Uploading Files

Use the interface (or API endpoint) to upload `.txt` or `.pdf` documents. They will be indexed and made searchable.

### Asking Legal Questions

You can now ask:

* "What is the precedent on self-defense?"
* "Summarize the 2014 criminal case in Delhi."
* "Which cases mention Article 21?"

And receive accurate, relevant results from your corpus.

---

## 💡 Example Use Cases

* **For Lawyers:** Quickly pull up case law supporting your current argument.
* **For Students:** Study relevant precedents and understand the evolution of legal thought.
* **For Academics:** Search vast amounts of legal data for thematic research.

---

## 🧠 Behind the Scenes

* **Embeddings:** Legal texts are converted into dense vector representations using transformer-based models.
* **FAISS Index:** Used to perform efficient similarity searches over these vectors.
* **Chunking Strategy:** Long documents are split into manageable sections (e.g., 512 tokens), so even small, relevant sections can be found.

---

## 🛡 License

This project is licensed under the Apache License 2.0.
See the LICENSE file for more details.

---

## 🤝 Contributing

Have suggestions or want to contribute? Please fork the repo and submit a pull request, or open an issue with your idea.

