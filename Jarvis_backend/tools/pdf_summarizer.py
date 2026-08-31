from tools.file_manager import resolve_and_verify_path

try:
    from pypdf import PdfReader
except ModuleNotFoundError:
    from PyPDF2 import PdfReader

from utils.logger import get_logger

logger = get_logger()

def extract_pdf_text(file_path: str) -> str:
    """
    Reads text from a local PDF file.
    
    Args:
        file_path (str): Path to the PDF file.
        
    Returns:
        str: Extracted text contents of the PDF or error message.
    """
    try:
        # Re-use our centralized path resolver for file safety
        safe_path = resolve_and_verify_path(file_path)
        
        if not safe_path.exists():
            return f"Error: PDF file not found at '{file_path}'"
        if not safe_path.is_file():
            return f"Error: Path is not a file: '{file_path}'"
            
        logger.info(f"Reading PDF: {safe_path}")
        reader = PdfReader(safe_path)
        
        extracted_pages = []
        for index, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(f"--- Page {index+1} ---\n{page_text}")
                
        full_text = "\n\n".join(extracted_pages).strip()
        
        if not full_text:
            return "Failed to extract text. The PDF may be scanned or image-based."
            
        # Capping the text to prevent token overhead
        if len(full_text) > 40000:
            full_text = full_text[:40000] + "\n\n[PDF text truncated due to size constraints]"
            
        return full_text
        
    except PermissionError as pe:
        return str(pe)
    except Exception as e:
        logger.error(f"Error reading PDF file {file_path}: {e}")
        return f"Failed to parse PDF file: {str(e)}"
