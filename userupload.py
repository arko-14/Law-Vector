import os
import requests
import pdfplumber

# Add your Hugging Face API token
HF_API_TOKEN = "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"
HF_MODEL = "facebook/bart-large-cnn"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

HEADERS = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

def extract_text_from_pdf(path: str) -> str:
    """Return full text of the PDF at path."""
    text = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text.append(page_text)
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""
    return "\n".join(text)

def summarize_text(text: str, max_length=512) -> str:
    """
    Generate a brief summary of text via Hugging Face Inference API.
    """
    if not text.strip():
        return "No text to summarize."

    chunk = text[:1024]
    payload = {
        "inputs": chunk,
        "parameters": {"max_length": max_length, "min_length": 80}
    }

    try:
        response = requests.post(HF_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and "summary_text" in result[0]:
            return result[0]["summary_text"]
        else:
            return "Unexpected response format."
    except Exception as e:
        print(f"Error calling HF Inference API: {e}")
        return "Error generating summary."

def prepare_prompt(user_question: str, context: str, summary: str = None) -> str:
    """
    Build the final prompt that goes to Sonar:
      - If summary is provided, prepend it.
      - Always include the most relevant context chunks.
    """
    parts = []
    if summary:
        parts.append(f"Document Summary:\n{summary}\n")
    parts.append(f"Relevant Excerpts:\n{context}\n")
    parts.append(f"User Question:\n{user_question}")
    return "\n\n".join(parts)

