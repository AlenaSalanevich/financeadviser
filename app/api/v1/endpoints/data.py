from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

# TODO: Import and apply auth dependency once auth is implemented, e.g.:
# from app.dependencies import get_current_user
# from fastapi import Depends

DATA_DIR = Path(__file__).resolve().parents[4] / "data"
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

router = APIRouter()


class UploadResponse(BaseModel):
    filename: str
    size_bytes: int
    message: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "bank_statement_jan_2026.pdf",
                "size_bytes": 204800,
                "message": "File 'bank_statement_jan_2026.pdf' uploaded successfully.",
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
        "The file is saved to the server's `data/` directory and can subsequently "
        "be indexed into the RAG vectorstore via the data loader script.\n\n"
        "**Constraints**\n"
        "- Only `application/pdf` files are accepted.\n"
        "- Maximum file size: **50 MB**.\n\n"
        "**Authentication**: Not required at this time. "
        "JWT-based auth will be enforced in a future release."
    ),
    responses={
        201: {
            "description": "PDF uploaded and saved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "filename": "bank_statement_jan_2026.pdf",
                        "size_bytes": 204800,
                        "message": "File 'bank_statement_jan_2026.pdf' uploaded successfully.",
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
            "description": "Server failed to write the file to disk.",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to save the file. Please try again."}
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

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destination = DATA_DIR / file.filename

    try:
        destination.write_bytes(contents)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save the file. Please try again.",
        ) from exc

    return UploadResponse(
        filename=file.filename,
        size_bytes=len(contents),
        message=f"File '{file.filename}' uploaded successfully.",
    )