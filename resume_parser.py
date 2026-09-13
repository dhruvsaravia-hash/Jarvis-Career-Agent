from pathlib import Path
import pdfplumber
from docx import Document

def extract_resume_text(file_path):
    path=Path(file_path)
    
    if not path.is_file():
        raise FileNotFoundError(f"Resume not found: {path}")
    
    extension = path.suffix.lower()
    
    if extension==".pdf":
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
        
    elif extension==".docx":
        document=Document(path)
        
        return "\n".join(
                        paragraph.text
                        for paragraph in document.paragraphs
                        if paragraph.text.strip()
        )
        
    else:
        raise ValueError("Unsupported resume format. please use pdf or docx.")        