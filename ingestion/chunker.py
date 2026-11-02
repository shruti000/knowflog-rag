
import hashlib
from dataclasses import dataclass
from typing import Any


@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]


class DocumentChunker:
    def __init__(
            self,
            chunk_size: int = 1000,
            chunk_overlap: int = 100,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be non-negative "
                "and smaller than chunk_size"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @staticmethod
    def _get(obj, *names, default=None):
        for name in names:
            if isinstance(obj, dict) and name in obj:
                return obj[name]
            if hasattr(obj, name):
                return getattr(obj, name)
        return default

    @staticmethod
    def _is_heading(lines: list[str], index: int) -> bool:
        line = lines[index].strip()

        if not line or len(line) > 60:
            return False

        if not any(char.isalpha() for char in line):
            return False

        if not line.isupper():
            return False

        # Find the next non-empty line.
        for next_index in range(index + 1, len(lines)):
            next_line = lines[next_index].strip()

            if not next_line:
                continue

            # A heading is more likely when normal sentence
            # text follows it, rather than another uppercase line.
            return any(char.islower() for char in next_line)

        return False

    def _split_text(self, text: str) -> list[str]:
        text = text.strip()

        if not text:
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            # Prefer splitting at a paragraph or word boundary.
            if end < len(text):
                boundary = max(
                    text.rfind("\n", start, end),
                    text.rfind(" ", start, end),
                )

                if boundary > start:
                    end = boundary

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            # Advance while retaining the configured overlap.
            next_start = max(start + 1, end - self.chunk_overlap)

            # Avoid starting the next chunk in the middle of a word.
            while (
                    next_start < end
                    and next_start > 0
                    and not text[next_start - 1].isspace()
                    and not text[next_start].isspace()
            ):
                next_start += 1

            start = next_start

        return chunks

    def _split_by_heading(self, text: str):
        lines = text.splitlines()

        current_heading = None
        current_lines = []

        for index, line in enumerate(lines):
            if self._is_heading(lines, index):
                if current_lines:
                    yield current_heading, "\n".join(current_lines).strip()

                current_heading = line.strip()
                current_lines = [line.strip()]
            else:
                current_lines.append(line)

        if current_lines:
            yield current_heading, "\n".join(current_lines).strip()

    def chunk_document(self, document) -> list[DocumentChunk]:
        chunks = []

        document_id = self._get(
            document, "document_id", default=""
        )
        source_document_id = self._get(
            document, "source_document_id", default=document_id
        )
        file_name = self._get(
            document, "file_name", "name", default="unknown"
        )
        source = self._get(document, "source", default="unknown")
        content_hash = self._get(
            document, "content_hash", default=""
        )
        last_modified = self._get(
            document, "last_modified", default=None
        )
        document_metadata = self._get(
            document, "metadata", default={}
        ) or {}

        sections = self._get(document, "sections", default=[])

        for page_index, page in enumerate(sections, start=1):
            if isinstance(page, str):
                page_text = page
                page_number = page_index
            else:
                page_text = self._get(
                    page, "content", "text", default=""
                )
                page_number = self._get(
                    page,
                    "page_number",
                    "page",
                    default=page_index,
                )

            if not page_text or not page_text.strip():
                continue

            # Detect headings within this page.
            for heading, section_text in self._split_by_heading(
                    page_text
            ):
                if not section_text:
                    continue

                # Split oversized sections into smaller chunks.
                text_chunks = self._split_text(section_text)

                for chunk_text in text_chunks:
                    chunk_id = hashlib.sha256(
                        (
                            f"{document_id}|{page_number}|"
                            f"{heading or ''}|{chunk_text}"
                        ).encode("utf-8")
                    ).hexdigest()

                    metadata = {
                        **document_metadata,
                        "document_id": document_id,
                        "source_document_id": source_document_id,
                        "source": str(
                            getattr(source, "value", source)
                        ),
                        "file_name": file_name,
                        "file_type": "pdf",
                        "page_number": page_number,
                        "section_heading": heading,
                        "content_hash": content_hash,
                        "last_modified": (
                            str(last_modified)
                            if last_modified is not None
                            else None
                        ),
                    }

                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            text=chunk_text,
                            metadata=metadata,
                        )
                    )

        return chunks
