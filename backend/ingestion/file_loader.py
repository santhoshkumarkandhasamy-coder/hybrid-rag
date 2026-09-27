from pathlib import Path
import subprocess
import tempfile
import shutil

from pypdf import PdfReader
from docx import Document
from openpyxl import load_workbook
from PIL import Image
import pytesseract


# ============================================================
# SUPPORTED FILE TYPES
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xlsx",
    ".png",
    ".jpg",
    ".jpeg",
}


# ============================================================
# FIND LIBREOFFICE
# ============================================================

def find_libreoffice() -> str:
    """
    Find LibreOffice executable on Windows or Linux.
    """

    # --------------------------------------------------------
    # 1. Check PATH
    # --------------------------------------------------------

    soffice = shutil.which("soffice")

    if soffice:
        return soffice

    # --------------------------------------------------------
    # 2. Windows installation locations
    # --------------------------------------------------------

    windows_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]

    for path in windows_paths:

        if Path(path).exists():
            return path

    # --------------------------------------------------------
    # 3. Linux / Docker locations
    # --------------------------------------------------------

    linux_paths = [
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
    ]

    for path in linux_paths:

        if Path(path).exists():
            return path

    raise RuntimeError(
        "LibreOffice is not installed or could not be found."
    )


# ============================================================
# CONVERT DOC → DOCX
# ============================================================

def convert_doc_to_docx(file_path: str) -> str:
    """
    Convert legacy .DOC file to .DOCX using LibreOffice.
    """

    input_path = Path(file_path)

    if not input_path.exists():

        raise FileNotFoundError(
            f"DOC file not found: {file_path}"
        )

    # Find LibreOffice
    libreoffice = find_libreoffice()

    # Temporary output directory
    output_dir = Path(
        tempfile.mkdtemp(
            prefix="doc_conversion_"
        )
    )

    command = [
        libreoffice,
        "--headless",
        "--convert-to",
        "docx",
        "--outdir",
        str(output_dir),
        str(input_path),
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
        )

    except subprocess.TimeoutExpired:

        raise RuntimeError(
            "LibreOffice conversion timed out."
        )

    except Exception as e:

        raise RuntimeError(
            f"Unable to start LibreOffice: {e}"
        )

    # Check LibreOffice result
    if result.returncode != 0:

        raise RuntimeError(
            "DOC conversion failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    # Expected DOCX path
    converted_file = (
        output_dir /
        f"{input_path.stem}.docx"
    )

    if not converted_file.exists():

        raise RuntimeError(
            "LibreOffice did not create the DOCX file.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    return str(converted_file)


# ============================================================
# PDF
# ============================================================

def extract_pdf(file_path: str) -> dict:

    reader = PdfReader(file_path)

    pages = []

    page_count = len(reader.pages)

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):

        text = page.extract_text() or ""

        if text.strip():

            pages.append(
                f"[Page {page_number}]\n{text}"
            )

    return {
        "file_type": "pdf",
        "pages": page_count,
        "text": "\n\n".join(pages),
    }


# ============================================================
# DOCX
# ============================================================

def extract_docx(file_path: str) -> dict:

    document = Document(file_path)

    sections = []

    # --------------------------------------------------------
    # Paragraphs
    # --------------------------------------------------------

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if text:

            sections.append(text)

    # --------------------------------------------------------
    # Tables
    # --------------------------------------------------------

    for table_index, table in enumerate(
        document.tables,
        start=1,
    ):

        sections.append(
            f"\n[Table {table_index}]"
        )

        for row in table.rows:

            row_values = []

            for cell in row.cells:

                row_values.append(
                    cell.text.strip()
                )

            sections.append(
                " | ".join(row_values)
            )

    return {
        "file_type": "docx",
        "pages": None,
        "text": "\n".join(sections),
    }


# ============================================================
# XLSX
# ============================================================

def extract_xlsx(file_path: str) -> dict:

    workbook = load_workbook(
        filename=file_path,
        data_only=True,
    )

    sections = []

    for worksheet in workbook.worksheets:

        sections.append(
            f"\n[Worksheet: {worksheet.title}]"
        )

        for row in worksheet.iter_rows(
            values_only=True
        ):

            values = []

            for value in row:

                if value is not None:

                    values.append(
                        str(value)
                    )

            if values:

                sections.append(
                    " | ".join(values)
                )

    return {
        "file_type": "xlsx",
        "pages": None,
        "text": "\n".join(sections),
    }


# ============================================================
# IMAGE OCR
# ============================================================

def extract_image(file_path: str) -> dict:

    image = Image.open(file_path)

    text = pytesseract.image_to_string(
        image
    )

    return {
        "file_type": "image",
        "pages": None,
        "text": text,
    }


# ============================================================
# UNIVERSAL FILE LOADER
# ============================================================

def extract_file_data(file_path: str) -> dict:

    path = Path(file_path)

    if not path.exists():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = path.suffix.lower()

    # --------------------------------------------------------
    # Validate extension
    # --------------------------------------------------------

    if extension not in SUPPORTED_EXTENSIONS:

        raise ValueError(
            f"Unsupported file type: {extension}. "
            "Supported formats: "
            "PDF, DOC, DOCX, XLSX, PNG, JPG, JPEG"
        )

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    if extension == ".pdf":

        return extract_pdf(
            file_path
        )

    # --------------------------------------------------------
    # Legacy DOC
    # --------------------------------------------------------

    if extension == ".doc":

        converted_docx = (
            convert_doc_to_docx(
                file_path
            )
        )

        return extract_docx(
            converted_docx
        )

    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    if extension == ".docx":

        return extract_docx(
            file_path
        )

    # --------------------------------------------------------
    # XLSX
    # --------------------------------------------------------

    if extension == ".xlsx":

        return extract_xlsx(
            file_path
        )

    # --------------------------------------------------------
    # Images
    # --------------------------------------------------------

    if extension in {
        ".png",
        ".jpg",
        ".jpeg",
    }:

        return extract_image(
            file_path
        )

    raise ValueError(
        f"Unsupported file extension: {extension}"
    )