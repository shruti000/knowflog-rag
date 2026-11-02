from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractedDocument:
    """Normalized output shared by all format extractors."""

    document_id: str
    source: str
    source_document_id: str
    file_name: str
    file_type: str
    content_hash: str
    last_modified: str | None
    sections: list[dict[str, Any]]
    extraction_status: str = "success"
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
