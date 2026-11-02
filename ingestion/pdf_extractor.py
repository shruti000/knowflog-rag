from io import BytesIO
import hashlib
from pathlib import Path
from typing import Any

import pymupdf

from ingestion.models import ExtractedDocument


def format_table(rows: list[list[Any] | tuple[Any, ...] | None]) -> str:
    """Convert extracted table rows to readable, label-value text."""
    if not rows:
        return ""

    first_row = rows[0] or []
    headers = [
        str(header).strip()
        if header is not None and str(header).strip()
        else f"Column_{index + 1}"
        for index, header in enumerate(first_row)
    ]

    formatted_rows: list[str] = []
    for row_number, row in enumerate(rows[1:], start=1):
        if not row:
            continue
        fields = []
        for header, value in zip(headers, row):
            if value is not None and str(value).strip():
                fields.append(f"{header}: {str(value).strip()}")
        if fields:
            formatted_rows.append(
                f"Record {row_number}: " + "; ".join(fields)
            )

    return "\n".join(formatted_rows)


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 in bounded file reads."""
    digest = hashlib.sha256()
    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class PDFExtractor:
    def extract(
        self,
        pdf_path: Path,
        *,
        source: str,
        source_document_id: str,
        file_name: str,
        content_type: str | None = "application/pdf",
        last_modified: str | None = None,
        etag: str | None = None,
    ) -> ExtractedDocument:
        pdf_path = Path(pdf_path)
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        file_size = pdf_path.stat().st_size
        content_hash = calculate_file_hash(pdf_path)
        sections: list[dict[str, Any]] = []
        errors: list[str] = []

        with pymupdf.open(pdf_path) as pdf_document:
            page_count = pdf_document.page_count

            for page_number, page in enumerate(pdf_document, start=1):
                content_parts: list[str] = []

                text_content = page.get_text("text").strip()
                if text_content:
                    content_parts.append(text_content)

                try:
                    table_finder = page.find_tables()
                    for table_number, table in enumerate(
                        table_finder.tables, start=1
                    ):
                        formatted_table = format_table(table.extract())
                        if formatted_table:
                            content_parts.append(
                                f"Table {table_number}:\n{formatted_table}"
                            )
                except Exception as exc:
                    errors.append(
                        f"Page {page_number}: table extraction failed "
                        f"({type(exc).__name__})."
                    )

                # Extract OCR text from embedded image resources.
                # This does not perform full-page OCR for scanned PDFs.
                for image_number, image_info in enumerate(
                    page.get_images(full=True), start=1
                ):
                    xref = image_info[0]
                    try:
                        image_data = pdf_document.extract_image(xref)
                        image_bytes = image_data["image"]

                        # Import OCR dependencies only when an image is present.
                        from PIL import Image
                        import pytesseract

                        with Image.open(BytesIO(image_bytes)) as image:
                            image_text = pytesseract.image_to_string(image).strip()

                        if image_text:
                            content_parts.append(
                                f"Image {image_number} OCR text:\n{image_text}"
                            )
                    except Exception as exc:
                        errors.append(
                            f"Page {page_number}, image {image_number}: OCR failed "
                            f"({type(exc).__name__})."
                        )

                sections.append(
                    {
                        "section_type": "page",
                        "page_number": page_number,
                        "content": "\n\n".join(content_parts),
                    }
                )

        return ExtractedDocument(
            document_id=content_hash,
            source=source,
            source_document_id=source_document_id,
            file_name=file_name,
            file_type="pdf",
            content_hash=content_hash,
            last_modified=last_modified,
            sections=sections,
            extraction_status="partial" if errors else "success",
            errors=errors,
            metadata={
                "content_type": content_type,
                "size_bytes": file_size,
                "etag": etag,
                "page_count": page_count,
            },
        )
