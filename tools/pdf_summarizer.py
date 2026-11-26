from pypdf import PdfReader

from utils.logger import get_logger
from utils.tool_response import tool_success, tool_error

from security.path_security import (
    resolve_and_verify_path,
    validate_file_size,
    MAX_PDF_BYTES,
    MAX_PDF_PAGES,
)


logger = get_logger()

MAX_EXTRACTED_CHARACTERS = 40000


def extract_pdf_text(file_path: str):
    """
    Securely extract text from an approved local PDF.
    """

    try:

        # Validate the file location.
        safe_path = resolve_and_verify_path(file_path)

        if not safe_path.is_file():
            return tool_error(
                "PDF file does not exist.",
                "FILE_NOT_FOUND"
            )

        # Validate the extension.
        if safe_path.suffix.lower() != ".pdf":
            return tool_error(
                "Only PDF files are supported.",
                "INVALID_FILE_TYPE"
            )

        # Validate the file size.
        file_size = validate_file_size(
            safe_path,
            MAX_PDF_BYTES
        )

        extracted_pages = []
        total_characters = 0
        pages_processed = 0
        truncated = False

        with safe_path.open("rb") as pdf_file:

            # Verify the PDF signature.
            if pdf_file.read(5) != b"%PDF-":
                return tool_error(
                    "Invalid PDF file signature.",
                    "INVALID_PDF"
                )

            pdf_file.seek(0)

            reader = PdfReader(pdf_file)

            # Reject encrypted PDFs.
            if reader.is_encrypted:
                return tool_error(
                    "Encrypted PDFs are not supported.",
                    "ENCRYPTED_PDF"
                )

            total_pages = len(reader.pages)

            if total_pages == 0:
                return tool_error(
                    "The PDF contains no pages.",
                    "EMPTY_PDF"
                )

            page_limit = min(
                total_pages,
                MAX_PDF_PAGES
            )

            if total_pages > page_limit:
                truncated = True

            # Extract only within approved limits.
            for index in range(page_limit):

                remaining = (
                    MAX_EXTRACTED_CHARACTERS
                    - total_characters
                )

                if remaining <= 0:
                    truncated = True
                    break

                page = reader.pages[index]

                page_text = page.extract_text() or ""

                pages_processed += 1

                if not page_text.strip():
                    continue

                formatted_text = (
                    f"\n\n--- Page {index + 1} ---\n"
                    f"{page_text}"
                )

                if len(formatted_text) > remaining:
                    formatted_text = formatted_text[:remaining]
                    truncated = True

                extracted_pages.append(formatted_text)

                total_characters += len(formatted_text)

                if total_characters >= MAX_EXTRACTED_CHARACTERS:
                    if index + 1 < total_pages:
                        truncated = True
                    break

        full_text = "".join(extracted_pages).strip()

        if not full_text:
            return tool_error(
                "No readable text found. "
                "The PDF may be scanned or image-based.",
                "NO_TEXT_FOUND"
            )

        logger.info(
            "PDF SECURITY | Extraction successful | "
            "Pages processed: %s | Characters: %s",
            pages_processed,
            len(full_text)
        )

        return tool_success(
            "PDF text extracted successfully.",
            {
                "filename": safe_path.name,
                "file_size_bytes": file_size,
                "total_pages": total_pages,
                "pages_processed": pages_processed,
                "characters_extracted": len(full_text),
                "truncated": truncated,
                "content": full_text
            }
        )

    except PermissionError:

        logger.warning(
            "PDF SECURITY | Unauthorized access blocked"
        )

        return tool_error(
            "PDF access denied by ASTRA security policy.",
            "ACCESS_DENIED"
        )

    except Exception:

        logger.exception("PDF extraction failed")

        return tool_error(
            "Unable to extract text from the PDF.",
            "PDF_EXTRACTION_ERROR"
        )