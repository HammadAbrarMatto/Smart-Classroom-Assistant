import requests
from bs4 import BeautifulSoup
import io

def fetch_url_content(url: str) -> dict:
    """
    Fetch and extract clean readable text from a webpage URL.

    Args:
        url (str): The webpage URL to fetch.

    Returns:
        dict: {"success": bool, "text": str, "title": str, "error": str or None}
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract page title
        title = soup.title.string.strip() if soup.title else "Untitled Page"

        # Remove unwanted tags
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "form", "noscript", "iframe", "ads"]):
            tag.decompose()

        # Extract main text from paragraphs
        paragraphs = soup.find_all(["p", "h1", "h2", "h3", "h4", "li", "article"])
        text_parts = [p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(strip=True)]
        full_text = "\n".join(text_parts)

        # Fallback: get all body text
        if not full_text.strip():
            full_text = soup.get_text(separator=" ", strip=True)

        # Trim to reasonable length (first 3000 chars)
        full_text = full_text[:3000].strip()

        if not full_text:
            return {"success": False, "text": "", "title": title,
                    "error": "No readable text found on the page."}

        return {"success": True, "text": full_text, "title": title, "error": None}

    except requests.exceptions.MissingSchema:
        return {"success": False, "text": "", "title": "",
                "error": "❌ Invalid URL. Make sure it starts with http:// or https://"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "text": "", "title": "",
                "error": "🌐 Could not connect. Check your internet connection or the URL."}
    except requests.exceptions.Timeout:
        return {"success": False, "text": "", "title": "",
                "error": "⏱️ Request timed out. The website took too long to respond."}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "text": "", "title": "",
                "error": f"🔴 HTTP Error {e.response.status_code}: {str(e)}"}
    except Exception as e:
        return {"success": False, "text": "", "title": "",
                "error": f"❌ Unexpected error: {str(e)}"}


def extract_pdf_text(file_bytes: bytes) -> dict:
    """
    Extract text from an uploaded PDF file (bytes).

    Args:
        file_bytes (bytes): Raw bytes of the PDF file.

    Returns:
        dict: {"success": bool, "text": str, "pages": int, "error": str or None}
    """
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            total_pages = len(pdf.pages)
            for page in pdf.pages[:10]:  # Limit to first 10 pages
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())

        full_text = "\n\n".join(text_parts)[:3000].strip()

        if not full_text:
            return {"success": False, "text": "", "pages": 0,
                    "error": "No extractable text found in the PDF (may be image-based)."}

        return {"success": True, "text": full_text, "pages": total_pages, "error": None}

    except ImportError:
        return {"success": False, "text": "", "pages": 0,
                "error": "pdfplumber not installed. Run: pip install pdfplumber"}
    except Exception as e:
        return {"success": False, "text": "", "pages": 0,
                "error": f"PDF extraction error: {str(e)}"}


def extract_txt_text(file_bytes: bytes) -> dict:
    """Extract text from a .txt file."""
    try:
        text = file_bytes.decode("utf-8", errors="ignore")[:3000].strip()
        if not text:
            return {"success": False, "text": "", "error": "The text file appears to be empty."}
        return {"success": True, "text": text, "error": None}
    except Exception as e:
        return {"success": False, "text": "", "error": f"Text file error: {str(e)}"}


def extract_docx_text(file_bytes: bytes) -> dict:
    """Extract text from a .docx Word file."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs)[:3000].strip()
        if not full_text:
            return {"success": False, "text": "", "error": "No text found in the Word document."}
        return {"success": True, "text": full_text, "error": None}
    except ImportError:
        return {"success": False, "text": "",
                "error": "python-docx not installed. Run: pip install python-docx"}
    except Exception as e:
        return {"success": False, "text": "", "error": f"DOCX extraction error: {str(e)}"}
