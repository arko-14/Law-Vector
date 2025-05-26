import pdfplumber
from transformers import pipeline

# Summarizer pipeline (facebook/bart-large-cnn)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

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
    Generate a brief summary of text.
    BART will chunk internally if needed.
    """
    if not text.strip():
        return "No text to summarize."

    try:
        # Truncate text if it exceeds the maximum length
        if len(text) > 1024:  # Example length limit, adjust as needed
            text = text[:1024]

        summary = summarizer(text, max_length=max_length, min_length=30, do_sample=False)
        return summary[0]["summary_text"]
    except Exception as e:
        print(f"Error summarizing text: {e}")
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