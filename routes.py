from fastapi import APIRouter, HTTPException

from ai_core.gemini_generator import GeminiDocumentGenerator
from backend.schemas import DocumentRequest, DocumentResponse
from backend.settings import settings


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# GEMINI DOCUMENT GENERATOR
# ============================================================

generator = GeminiDocumentGenerator(settings)


# ============================================================
# HEALTH CHECK
# ============================================================

@router.get(
    "/health",
    tags=["system"],
)
def health():
    """
    Check whether the LegalEase backend is running
    and whether Gemini has been configured.
    """

    return {
        "status": "ok",
        "gemini_configured": bool(
            settings.gemini_api_key
        ),
        "model": settings.gemini_model,
    }


# ============================================================
# DOCUMENT GENERATION
# ============================================================

@router.post(
    "/generate",
    response_model=DocumentResponse,
    tags=["documents"],
)
def generate_document(
    request: DocumentRequest,
):
    """
    Generate a legal document using Gemini.

    Request:
        document_type
        parties
        terms
        dates
        logo_base64 (optional)

    Response:
        document_type
        content
    """

    try:

        content = generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            dates=request.dates,
        )

        return DocumentResponse(
            document_type=request.document_type,
            content=content,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected error occurred "
                "while generating the document."
            ),
        ) from exc