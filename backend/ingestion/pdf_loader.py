from pathlib import Path

from pypdf import PdfReader


def extract_pdf_data(pdf_path: str) -> dict:
    """
    Extract text and metadata from a PDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Dictionary containing page count and extracted text.
    """

    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(
            f"PDF file not found: {pdf_path}"
        )

    reader = PdfReader(str(pdf_file))

    pages = []
    page_count = len(reader.pages)

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    full_text = "\n\n".join(pages)

    return {
        "pages": page_count,
        "text": full_text,
    }