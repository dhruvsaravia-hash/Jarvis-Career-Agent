from pathlib import Path
import pdfplumber

def extract_resume_text(pdf_path):
    path=Path(pdf_path)
    
    if not path.is_file():
        raise FileNotFoundError(f"Resume not found: {path}")
    
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)