#
# from pathlib import Path
# from ingestion.pdf_extractor import PDFExtractor
#
# pdf_path = Path("data/downloads/downloaded_HR-Policy.pdf")
#
# extractor = PDFExtractor()
#
# document = extractor.extract(
#     pdf_path=pdf_path,
#     source="azure_blob",
#     source_document_id="HR-Policy.pdf",
#     file_name="HR-Policy.pdf",
# )
#
# print("Extraction successful!")
# print("File name:", document.file_name)
# print("Page count:", document.metadata["page_count"])
# print("Number of sections:", len(document.sections))
#
# output_path = Path("data/extracted/HR-Policy.txt")
# output_path.parent.mkdir(parents=True, exist_ok=True)
#
# with output_path.open("w", encoding="utf-8") as f:
#     for section in document.sections:
#         f.write(section["content"])
#         f.write("\n\n")
#
# print("Extracted text saved to:", output_path.resolve())
