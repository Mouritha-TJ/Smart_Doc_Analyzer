import os
import PyPDF2
import docx

def extract_document_content(file_path: str) -> dict:
    """
    Extracts text and page mapping from PDF, DOCX, or TXT files.
    Returns:
        {
            "full_text": str,
            "pages": [{"page": int, "text": str}],
            "file_type": str
        }
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = file_path.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        return _extract_pdf(file_path)
    elif ext == "docx":
        return _extract_docx(file_path)
    elif ext == "txt":
        return _extract_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: .{ext}")

def _extract_pdf(file_path: str) -> dict:
    pages_data = []
    full_text_list = []

    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            if len(reader.pages) == 0:
                raise ValueError("The PDF document is empty (0 pages).")

            for idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                page_text_clean = page_text.strip()
                if page_text_clean:
                    pages_data.append({"page": idx, "text": page_text_clean})
                    full_text_list.append(page_text_clean)

        full_text = "\n\n".join(full_text_list).strip()
        if not full_text:
            raise ValueError("No extractable text was found in the PDF. It may contain scanned images only.")

        return {
            "full_text": full_text,
            "pages": pages_data,
            "file_type": "pdf"
        }
    except PyPDF2.errors.PdfReadError:
        raise ValueError("The file appears to be corrupted or is not a valid PDF.")

def _extract_docx(file_path: str) -> dict:
    try:
        doc = docx.Document(file_path)
        full_text_list = []
        pages_data = []

        # DOCX doesn't strictly have page numbers in raw text, so we chunk every ~300 words or 5 paragraphs into a virtual page
        current_page_paras = []
        current_page_words = 0
        current_page_num = 1

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            current_page_paras.append(text)
            words = len(text.split())
            current_page_words += words

            if current_page_words >= 350:
                page_str = "\n".join(current_page_paras)
                pages_data.append({"page": current_page_num, "text": page_str})
                full_text_list.append(page_str)
                current_page_paras = []
                current_page_words = 0
                current_page_num += 1

        if current_page_paras:
            page_str = "\n".join(current_page_paras)
            pages_data.append({"page": current_page_num, "text": page_str})
            full_text_list.append(page_str)

        full_text = "\n\n".join(full_text_list).strip()
        if not full_text:
            raise ValueError("No text content found in the DOCX file.")

        return {
            "full_text": full_text,
            "pages": pages_data,
            "file_type": "docx"
        }
    except Exception as e:
        raise ValueError(f"Error reading DOCX file: {str(e)}")

def _extract_txt(file_path: str) -> dict:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()

        if not text:
            raise ValueError("The TXT file is empty.")

        return {
            "full_text": text,
            "pages": [{"page": None, "text": text}],
            "file_type": "txt"
        }
    except Exception as e:
        raise ValueError(f"Error reading TXT file: {str(e)}")

# Legacy compatibility function
def extract_text_from_pdf(file_path: str) -> str:
    res = extract_document_content(file_path)
    return res["full_text"]
