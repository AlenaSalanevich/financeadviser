from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.loader import embed_pdf

# TODO: Import and apply auth dependency once auth is implemented, e.g.:
# from app.dependencies import get_current_user
# from fastapi import Depends

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

router = APIRouter()


class UploadResponse(BaseModel):
    filename: str
    size_bytes: int
    chunks_stored: int
    message: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "bank_statement_jan_2026.pdf",
                "size_bytes": 204800,
                "chunks_stored": 12,
                "message": "File 'bank_statement_jan_2026.pdf' uploaded and embedded (12 chunks).",
            }
        }
    }


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF document",
    description=(
        "Upload a PDF file for financial document analysis.\n\n"
        "The file is processed in memory: text is extracted, split into chunks, "
        "embedded with OpenAI, and stored in Supabase via pgvector.\n\n"
        "**Constraints**\n"
        "- Only `application/pdf` files are accepted.\n"
        "- Maximum file size: **50 MB**.\n\n"
        "**Authentication**: Not required at this time. "
        "JWT-based auth will be enforced in a future release."
    ),
    responses={
        201: {
            "description": "PDF processed and embeddings stored successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "filename": "bank_statement_jan_2026.pdf",
                        "size_bytes": 204800,
                        "chunks_stored": 12,
                        "message": "File 'bank_statement_jan_2026.pdf' uploaded and embedded (12 chunks).",
                    }
                }
            },
        },
        400: {
            "description": "Invalid file — wrong type, missing `.pdf` extension, or empty.",
            "content": {
                "application/json": {
                    "example": {"detail": "Only PDF files are accepted."}
                }
            },
        },
        413: {
            "description": "File exceeds the 50 MB size limit.",
            "content": {
                "application/json": {
                    "example": {"detail": "File size 60000000 bytes exceeds the 50 MB limit."}
                }
            },
        },
        500: {
            "description": "Server failed to embed and store the file.",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to process the file. Please try again."}
                }
            },
        },
    },
)
async def upload_pdf(
    file: Annotated[
        UploadFile,
        File(description="PDF file to upload. Must be `application/pdf`, max 50 MB."),
    ],
    # TODO: enable when auth is ready:
    # current_user: User = Depends(get_current_user),
) -> UploadResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid content type '{file.content_type}'. Only PDF files are accepted."
            ),
        )

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a .pdf extension.",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {len(contents)} bytes exceeds the 50 MB limit.",
        )

    try:
        chunks_stored = await embed_pdf(contents, file.filename)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the file. Please try again.",
        ) from exc

    return UploadResponse(
        filename=file.filename,
        size_bytes=len(contents),
        chunks_stored=chunks_stored,
        message=f"File '{file.filename}' uploaded and embedded ({chunks_stored} chunks).",
    )
