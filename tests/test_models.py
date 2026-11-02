from ingestion.models import ExtractedDocument


def test_extracted_document_defaults():
    document = ExtractedDocument(
        document_id="id",
        source="azure_blob",
        source_document_id="policies/policy.pdf",
        file_name="policy.pdf",
        file_type="pdf",
        content_hash="hash",
        last_modified=None,
        sections=[],
    )

    assert document.extraction_status == "success"
    assert document.errors == []
    assert document.metadata == {}
