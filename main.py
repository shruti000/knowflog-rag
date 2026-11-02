
import json
from pathlib import Path

from ingestion.azure_blob_connector import AzureBlobConnector
from ingestion.document_detector import DocumentDetector
from ingestion.pdf_extractor import PDFExtractor
from ingestion.chunker import DocumentChunker
from embeddings.gemini_embedding import GeminiEmbedder
from indexing.indexing import AzureAIIndexer

def run_extraction(blob_name: str = "HR-Policy.pdf") -> None:
    connector = AzureBlobConnector()

    try:
        # Step 1: Detect the document type
        file_name = Path(blob_name).name
        document_type = DocumentDetector.detect(file_name)

        print("Detected document type:", document_type)

        # Step 2: Route to the appropriate extractor
        if document_type != "pdf":
            raise ValueError(
                f"No extraction flow configured for: {document_type}"
            )

        extractor = PDFExtractor()

        # Step 3: Create the PDF download folder
        project_dir = Path(__file__).resolve().parent

        download_dir = project_dir / "data" / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)

        # Step 4: Download the PDF from Azure Blob Storage
        pdf_path = download_dir / "HR-Policy-final4.pdf"

        connector.download_to_file(blob_name, pdf_path)

        print("PDF downloaded successfully.")
        print("PDF saved at:", pdf_path)

        # Step 5: Extract the PDF
        extracted_document = extractor.extract(
            pdf_path=pdf_path,
            source="azure_blob",
            source_document_id=blob_name,
            file_name=file_name,
        )

        print("\nPDF extraction completed.")
        print("File name:", extracted_document.file_name)
        print("Page count:", extracted_document.metadata["page_count"])
        print("Document ID:", extracted_document.document_id)

        # Step 6: Save extracted text to a TXT file
        extracted_dir = project_dir / "data" / "extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)

        text_path = extracted_dir / f"{Path(file_name).stem}.txt"

        with text_path.open("w", encoding="utf-8") as text_file:
            for section in extracted_document.sections:
                page_number = section.get("page_number")

                if page_number is not None:
                    text_file.write(
                        f"\n--- Page {page_number} ---\n\n"
                    )

                text_file.write(section["content"])
                text_file.write("\n\n")

        print("\nExtracted text saved successfully.")
        print("Text file path:", text_path)

        # Step 7: Chunk the extracted document
        chunker = DocumentChunker(
            chunk_size=1000,
            chunk_overlap=100,
        )

        chunks = chunker.chunk_document(extracted_document)

        print("\nChunking completed.")
        print("Total chunks created:", len(chunks))

        # Step 8: Save all chunks without truncation
        chunks_dir = project_dir / "data" / "chunks"
        chunks_dir.mkdir(parents=True, exist_ok=True)

        chunks_path = chunks_dir / "HR-Policy-chunks.txt"

        with chunks_path.open("w", encoding="utf-8") as output_file:
            for index, chunk in enumerate(chunks, start=1):
                output_file.write(f"Chunk number: {index}\n")
                output_file.write(f"Chunk ID: {chunk.chunk_id}\n")
                output_file.write(f"Metadata: {chunk.metadata}\n")
                output_file.write(f"Text:\n{chunk.text}\n")
                output_file.write("\n" + "=" * 80 + "\n\n")

        print("\nAll chunks saved successfully.")
        print("Chunk file path:", chunks_path)

        # Step 9: Generate embeddings and save them to JSON
        embedder = GeminiEmbedder()
        embedded_chunks = []

        for index, chunk in enumerate(chunks, start=1):
            embedded_chunk = embedder.embed_chunk(chunk)
            embedded_chunks.append(embedded_chunk)

            # print(f"Embedded chunk {index}/{len(chunks)}")

        embeddings_dir = project_dir / "data" / "embeddings"
        embeddings_dir.mkdir(parents=True, exist_ok=True)

        embeddings_path = (
                embeddings_dir / f"{Path(file_name).stem}-embeddings.json"
        )

        with embeddings_path.open("w", encoding="utf-8") as output_file:
            json.dump(
                embedded_chunks,
                output_file,
                ensure_ascii=False,
                indent=2,
            )

        print("\nEmbedding generation completed.")
        print("Total embeddings generated:", len(embedded_chunks))
        print("Embeddings saved at:", embeddings_path)


        # Step 7: Upload embeddings to Azure AI Search
        indexer = AzureAIIndexer()

        try:
            indexer.index_embeddings(limit=2)
        finally:
            indexer.close()

    finally:
        connector.close()


if __name__ == "__main__":
    run_extraction()
