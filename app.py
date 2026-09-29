from __future__ import annotations

import base64
import os
from datetime import date

import requests
import streamlit as st
from dotenv import load_dotenv

from services.document_export import (
    format_docx,
    format_pdf,
    format_txt,
)

from utils.text_utils import (
    html_preview,
    sanitize_text,
    terms_to_list,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# ============================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

def inject_css() -> None:
    st.markdown(
        """
        <style>

        .legal-preview {
            background: #111827;
            color: #f3f4f6;
            border-radius: 14px;
            padding: 28px;
            max-height: 650px;
            overflow-y: auto;
            line-height: 1.7;
            border: 1px solid #374151;
        }

        .legal-preview h3 {
            color: #ffffff;
            margin-top: 18px;
            margin-bottom: 10px;
        }

        .legal-preview p {
            margin-bottom: 14px;
        }

        .app-description {
            font-size: 1.05rem;
            color: #6b7280;
        }

        .status-box {
            padding: 12px;
            border-radius: 10px;
            margin-top: 10px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# BACKEND API
# ============================================================

def backend_generate(payload: dict) -> str:
    """
    Send document-generation request to the FastAPI backend.
    """

    response = requests.post(
        f"{BACKEND_URL}/generate",
        json=payload,
        timeout=180,
    )

    if response.status_code >= 400:
        try:
            data = response.json()
            detail = data.get(
                "detail",
                response.text,
            )
        except ValueError:
            detail = response.text

        raise RuntimeError(str(detail))

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Backend returned an invalid response."
        ) from exc

    if "content" not in data:
        raise RuntimeError(
            "Backend response did not contain generated document content."
        )

    return data["content"]


def check_backend() -> dict | None:
    """
    Check whether the FastAPI backend is reachable.
    """

    try:
        response = requests.get(
            f"{BACKEND_URL}/health",
            timeout=5,
        )

        if response.status_code != 200:
            return None

        return response.json()

    except requests.RequestException:
        return None


# ============================================================
# INITIALIZE SESSION STATE
# ============================================================

if "document" not in st.session_state:
    st.session_state["document"] = ""

if "document_type" not in st.session_state:
    st.session_state["document_type"] = ""

if "terms" not in st.session_state:
    st.session_state["terms"] = ""

if "logo_base64" not in st.session_state:
    st.session_state["logo_base64"] = None


# ============================================================
# CSS
# ============================================================

inject_css()


# ============================================================
# HEADER
# ============================================================

st.title("⚖️ LegalEase")

st.markdown(
    """
    <div class="app-description">
        AI-powered legal document drafting, editing and export.
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("📄 Document Details")

    st.caption(
        "Enter the information required to generate your legal document."
    )

    document_type = st.text_input(
        "Document Type",
        value="Non-Disclosure Agreement",
        placeholder="Example: Employment Contract",
        help=(
            "Examples: NDA, Employment Contract, "
            "Lease Agreement, Service Agreement."
        ),
    )

    parties = st.text_area(
        "Parties Involved",
        value=(
            "Jane Doe (Disclosing Party), "
            "TechNova Inc. (Receiving Party)"
        ),
        height=110,
        placeholder=(
            "Example: John Smith and ABC Technologies Ltd."
        ),
    )

    terms = st.text_area(
        "Terms & Conditions",
        value=(
            "Confidential information must be protected; "
            "Disclosure is limited to authorized personnel; "
            "The agreement is effective for two years"
        ),
        height=170,
        placeholder=(
            "Enter the important terms and conditions..."
        ),
        help=(
            "Separate terms with semicolons or put "
            "each term on a new line."
        ),
    )

    effective_date = st.date_input(
        "Effective Date",
        value=date.today(),
    )

    logo = st.file_uploader(
        "Optional Logo",
        type=[
            "png",
            "jpg",
            "jpeg",
        ],
        help=(
            "The logo will be embedded into DOCX and PDF exports."
        ),
    )

    st.divider()

    generate = st.button(
        "🚀 Generate Document",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# DISCLAIMER
# ============================================================

st.info(
    "⚠️ LegalEase creates AI-generated drafts for review. "
    "It does not replace advice from a qualified lawyer."
)


# ============================================================
# GENERATE DOCUMENT
# ============================================================

if generate:

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not document_type.strip():
        st.error(
            "Please enter a document type."
        )
        st.stop()

    if not parties.strip():
        st.error(
            "Please enter the parties involved."
        )
        st.stop()

    if not terms.strip():
        st.error(
            "Please enter the terms and conditions."
        )
        st.stop()

    # --------------------------------------------------------
    # Process logo
    # --------------------------------------------------------

    logo_base64 = None

    if logo is not None:

        raw_logo = logo.getvalue()

        # Limit logo size to approximately 5 MB.
        if len(raw_logo) > 5 * 1024 * 1024:

            st.error(
                "Logo file is too large. "
                "Please upload an image smaller than 5 MB."
            )

            st.stop()

        logo_base64 = (
            "data:"
            + logo.type
            + ";base64,"
            + base64.b64encode(
                raw_logo
            ).decode("utf-8")
        )

    # --------------------------------------------------------
    # API payload
    # --------------------------------------------------------

    payload = {
        "document_type": document_type.strip(),
        "parties": parties.strip(),
        "terms": terms.strip(),
        "dates": effective_date.isoformat(),
        "logo_base64": logo_base64,
    }

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    with st.spinner(
        "🤖 Generating your legal document with Gemini..."
    ):

        try:

            generated = backend_generate(
                payload
            )

            if not generated.strip():
                st.error(
                    "The AI returned an empty document."
                )
                st.stop()

            st.session_state["document"] = generated

            st.session_state["document_type"] = (
                document_type.strip()
            )

            st.session_state["terms"] = (
                terms.strip()
            )

            st.session_state["logo_base64"] = (
                logo_base64
            )

            st.success(
                "Document generated successfully."
            )

        except requests.Timeout:

            st.error(
                "The generation request timed out. "
                "Please try again."
            )

        except requests.ConnectionError:

            st.error(
                "Could not connect to the FastAPI backend."
            )

            st.caption(
                f"Expected backend: {BACKEND_URL}"
            )

        except requests.RequestException as exc:

            st.error(
                "A network error occurred while contacting the backend."
            )

            st.caption(str(exc))

        except RuntimeError as exc:

            st.error(
                str(exc)
            )

        except Exception as exc:

            st.error(
                "An unexpected error occurred."
            )

            st.caption(str(exc))


# ============================================================
# CURRENT DOCUMENT
# ============================================================

document = st.session_state.get(
    "document",
    "",
)


# ============================================================
# DOCUMENT VIEW
# ============================================================

if document:

    st.subheader(
        "📑 Generated Document"
    )

    tab_preview, tab_edit = st.tabs(
        [
            "👁️ Preview",
            "✏️ Edit",
        ]
    )

    # ========================================================
    # PREVIEW TAB
    # ========================================================

    with tab_preview:

        st.markdown(
            html_preview(document),
            unsafe_allow_html=True,
        )

    # ========================================================
    # EDIT TAB
    # ========================================================

    with tab_edit:

        edited = st.text_area(
            "Edit the generated document",
            value=document,
            height=600,
            key="document_editor",
        )

        if st.button(
            "💾 Save Edits",
            use_container_width=True,
        ):

            cleaned_document = sanitize_text(
                edited
            )

            if not cleaned_document:

                st.error(
                    "The document cannot be empty."
                )

            else:

                st.session_state["document"] = (
                    cleaned_document
                )

                st.success(
                    "Your edits have been saved to the current session."
                )

                st.rerun()


    # ========================================================
    # EXPORT SECTION
    # ========================================================

    st.divider()

    st.subheader(
        "⬇️ Download Document"
    )

    doc_type = st.session_state.get(
        "document_type",
        document_type,
    )

    current_terms = st.session_state.get(
        "terms",
        terms,
    )

    current_logo = st.session_state.get(
        "logo_base64",
        None,
    )

    # --------------------------------------------------------
    # Generate export files
    # --------------------------------------------------------

    try:

        txt_bytes = format_txt(
            document
        )

        docx_bytes = format_docx(
            document,
            doc_type,
            logo_base64=current_logo,
            terms=current_terms,
        )

        pdf_bytes = format_pdf(
            document,
            doc_type,
            logo_base64=current_logo,
            terms=current_terms,
        )

        export_error = None

    except Exception as exc:

        txt_bytes = None
        docx_bytes = None
        pdf_bytes = None

        export_error = exc


    # --------------------------------------------------------
    # Display export error
    # --------------------------------------------------------

    if export_error:

        st.error(
            "Could not prepare the document exports."
        )

        st.caption(
            str(export_error)
        )

    else:

        c1, c2, c3 = st.columns(3)

        # ----------------------------------------------------
        # TXT
        # ----------------------------------------------------

        with c1:

            st.download_button(
                label="📄 Download TXT",
                data=txt_bytes,
                file_name="legalease_document.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # ----------------------------------------------------
        # DOCX
        # ----------------------------------------------------

        with c2:

            st.download_button(
                label="📝 Download DOCX",
                data=docx_bytes,
                file_name="legalease_document.docx",
                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                use_container_width=True,
            )

        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        with c3:

            st.download_button(
                label="📕 Download PDF",
                data=pdf_bytes,
                file_name="legalease_document.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


    # ========================================================
    # TERMS TABLE
    # ========================================================

    parsed_terms = terms_to_list(
        current_terms
    )

    if parsed_terms:

        st.divider()

        with st.expander(
            "📋 Key Terms"
        ):

            for index, term in enumerate(
                parsed_terms,
                start=1,
            ):

                st.write(
                    f"**{index}.** {term}"
                )


# ============================================================
# EMPTY STATE
# ============================================================

else:

    st.subheader(
        "Create a Legal Document"
    )

    st.write(
        "Enter your document details in the sidebar, "
        "then click **Generate Document**."
    )

    st.write(
        "The generated document can be reviewed, edited, "
        "and exported as TXT, DOCX, or PDF."
    )

    st.divider()

    # ========================================================
    # BACKEND STATUS
    # ========================================================

    st.subheader(
        "🔌 System Status"
    )

    health = check_backend()

    if health:

        if health.get("gemini_configured"):

            st.success(
                "✅ Backend connected"
            )

            st.caption(
                "Gemini model: "
                + str(
                    health.get(
                        "model",
                        "Unknown",
                    )
                )
            )

        else:

            st.warning(
                "⚠️ Backend is reachable, "
                "but GEMINI_API_KEY is not configured."
            )

            st.caption(
                "Add your Gemini API key to the .env file."
            )

    else:

        st.warning(
            "⚠️ FastAPI backend is not currently reachable."
        )

        st.caption(
            f"Expected backend URL: {BACKEND_URL}"
        )

        st.code(
            "uvicorn backend.main:app "
            "--reload "
            "--host 127.0.0.1 "
            "--port 8000",
            language="powershell",
        )