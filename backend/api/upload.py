from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.ingestion.file_loader import (
    extract_file_data,
    SUPPORTED_EXTENSIONS,
)

from backend.ingestion.chunker import split_text
from backend.ingestion.vector_store import (
    create_vector_store,
    save_vector_store,
)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("data/uploads")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Supported formats: "
                "PDF, DOCX, XLSX, PNG, JPG, JPEG"
            ),
        )

    document_id = str(uuid4())

    # Keep each document in its own folder
    document_dir = UPLOAD_DIR / document_id
    document_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = Path(file.filename).name

    file_path = document_dir / safe_filename

    # Save uploaded file
    contents = await file.read()

    with open(file_path, "wb") as output_file:
        output_file.write(contents)

    try:

        # ---------------------------------
        # Extract text
        # ---------------------------------

        extracted = extract_file_data(
            str(file_path)
        )

        text = extracted["text"]

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text was found "
                    "in the uploaded file."
                ),
            )

        # ---------------------------------
        # Chunk text
        # ---------------------------------

        chunks = split_text(text)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No text chunks were created.",
            )

        # ---------------------------------
        # Create FAISS
        # ---------------------------------

        vector_store = create_vector_store(
            chunks
        )

        save_vector_store(
            vector_store,
            document_id,
        )

        # ---------------------------------
        # Response
        # ---------------------------------

        return {
            "document_id": document_id,
            "filename": safe_filename,
            "file_type": extracted["file_type"],
            "pages": extracted.get("pages"),
            "characters": len(text),
            "chunks": len(chunks),
            "status": "completed",
            "text": text,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {str(e)}",
        )