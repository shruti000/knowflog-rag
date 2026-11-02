import json
import os
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient


class AzureAIIndexer:
    def __init__(self):
        self.endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
        self.index_name = "knowflow-index"

        self.credential = DefaultAzureCredential()

        self.client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential,
        )

    def index_embeddings(self, limit: int | None = None) -> int:
        # Step 1: Locate the existing embeddings JSON
        project_dir = Path(__file__).resolve().parents[1]

        embeddings_path = (
                project_dir
                / "data"
                / "embeddings"
                / "HR-Policy-embeddings.json"
        )

        if not embeddings_path.exists():
            raise FileNotFoundError(
                f"Embeddings file not found: {embeddings_path}"
            )

        # Step 2: Load existing embeddings
        with embeddings_path.open("r", encoding="utf-8") as file:
            chunks = json.load(file)

        if not chunks:
            raise ValueError("The embeddings file is empty.")

        selected_chunks = chunks if limit is None else chunks[:limit]

        print(f"Embeddings available: {len(chunks)}")
        print(f"Chunks selected for indexing: {len(selected_chunks)}")

        # Step 3: Prepare documents for Azure AI Search
        documents = []

        for chunk in selected_chunks:
            metadata = chunk["metadata"]
            embedding = chunk["embedding"]

            if len(embedding) != 3072:
                raise ValueError(
                    f"Invalid embedding dimensions for "
                    f"{chunk['chunk_id']}: {len(embedding)}"
                )

            documents.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "embedding": embedding,
                "source": metadata["source"],
                "file_name": metadata["file_name"],
                "content_hash": metadata["content_hash"],
            })

        # Step 4: Upload documents
        print("Uploading documents to Azure AI Search...")

        results = self.client.upload_documents(documents=documents)

        for result in results:
            print(
                f"Chunk {result.key}: "
                f"{'SUCCESS' if result.succeeded else 'FAILED'}"
            )

            if not result.succeeded:
                raise RuntimeError(
                    f"Indexing failed for {result.key}: "
                    f"{result.error_message}"
                )

        # Step 5: Verify the index through the same SearchClient
        document_count = self.client.get_document_count()

        print(f"Documents currently in index: {document_count}")

        # Step 6: Verify that uploaded chunks can be retrieved
        indexed_ids = {
            document.get("chunk_id")
            for document in self.client.search(
                search_text="*",
                top=len(documents),
                select=["chunk_id"],
            )
        }

        missing_ids = {
                          document["chunk_id"] for document in documents
                      } - indexed_ids

        if missing_ids:
            raise RuntimeError(
                "Upload returned success, but these chunks were not "
                f"retrieved by search: {missing_ids}"
            )

        print(
            f"Successfully indexed and verified "
            f"{len(documents)} chunks."
        )

        return len(documents)

    def close(self):
        self.client.close()
        self.credential.close()











# Running directly

# import json
# import os
# from pathlib import Path
#
# from azure.identity import DefaultAzureCredential
# from azure.search.documents import SearchClient
#
#
# class AzureAIIndexer:
#     def __init__(self):
#         self.endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
#         self.index_name = "knowflow-index"
#
#         self.credential = DefaultAzureCredential()
#
#         self.client = SearchClient(
#             endpoint=self.endpoint,
#             index_name=self.index_name,
#             credential=self.credential,
#         )
#
#     def index_embeddings(self, limit: int = 2):
#         # Step 1: Locate the existing embeddings JSON
#         project_dir = Path(__file__).resolve().parents[1]
#
#         embeddings_path = (
#                 project_dir
#                 / "data"
#                 / "embeddings"
#                 / "HR-Policy-embeddings.json"
#         )
#
#         if not embeddings_path.exists():
#             raise FileNotFoundError(
#                 f"Embeddings file not found: {embeddings_path}"
#             )
#
#         print(f"Reading embeddings from: {embeddings_path}")
#
#         # Step 2: Load existing embeddings; do not regenerate them
#         with embeddings_path.open("r", encoding="utf-8") as file:
#             chunks = json.load(file)
#
#         print(f"Total embedded chunks in file: {len(chunks)}")
#
#         if not chunks:
#             raise ValueError("The embeddings file is empty.")
#
#         documents = []
#
#         # Step 3: Prepare a small batch for Azure AI Search
#         for chunk in chunks[:limit]:
#             metadata = chunk["metadata"]
#             embedding = chunk["embedding"]
#
#             if len(embedding) != 3072:
#                 raise ValueError(
#                     f"Invalid embedding dimensions for "
#                     f"{chunk['chunk_id']}: {len(embedding)}"
#                 )
#
#             documents.append({
#                 "chunk_id": chunk["chunk_id"],
#                 "text": chunk["text"],
#                 "embedding": embedding,
#                 "source": metadata["source"],
#                 "file_name": metadata["file_name"],
#                 "content_hash": metadata["content_hash"],
#             })
#
#         # Step 4: Upload documents
#         print(
#             f"\nUploading {len(documents)} chunks "
#             f"to Azure AI Search..."
#         )
#
#         results = self.client.upload_documents(
#             documents=documents
#         )
#
#         # Step 5: Check each upload result
#         for result in results:
#             print(f"\nDocument key: {result.key}")
#             print(f"Upload succeeded: {result.succeeded}")
#
#             if not result.succeeded:
#                 raise RuntimeError(
#                     f"Indexing failed for {result.key}: "
#                     f"{result.error_message}"
#                 )
#
#         print("\nUpload operations succeeded.")
#
#         # Step 6: Check the actual index document count
#         count = self.client.get_document_count()
#
#         print(f"Documents currently in Azure AI Search index: {count}")
#
#         # Step 7: Retrieve a document to verify it is searchable
#         print("\nVerifying uploaded documents...")
#
#         search_results = self.client.search(
#             search_text="*",
#             top=limit,
#             select=["chunk_id", "file_name", "source", "text"],
#         )
#
#         found_count = 0
#
#         for document in search_results:
#             found_count += 1
#
#             print(f"\nRetrieved document {found_count}")
#             print(f"Chunk ID: {document.get('chunk_id')}")
#             print(f"File: {document.get('file_name')}")
#             print(f"Source: {document.get('source')}")
#             print(
#                 f"Text preview: "
#                 f"{(document.get('text') or '')[:200]}"
#             )
#
#         print(f"\nDocuments returned by search: {found_count}")
#
#         if count == 0:
#             print(
#                 "\nWARNING: Azure AI Search reports zero documents. "
#                 "Check the index name, upload results, and permissions."
#             )
#
#         return count
#
#     def close(self):
#         self.client.close()
#         self.credential.close()
#
#
# if __name__ == "__main__":
#     indexer = AzureAIIndexer()
#
#     try:
#         indexer.index_embeddings(limit=2)
#     finally:
#         indexer.close()
