# KnowFlow — ingestion foundation

This reconstructed starter includes Azure Blob download-to-file and PDF extraction.
It is not a copy of the complete local project and does not yet implement chunking,
embeddings, Azure AI Search, API endpoints, or document-level authorization.

## Requirements

- Python 3.11+
- `uv`
- Azure access configured through Azure CLI locally (`az login`) or Managed Identity
  when running in Azure.
- Tesseract OCR installed on the operating system if image OCR is required.

## Setup

```bash
uv sync
cp .env.example .env
```

Fill `.env` with your storage account URL and container name. Do not add account keys
or other secrets to source control. `DefaultAzureCredential` uses your local Azure
CLI login during development and Managed Identity in Azure when configured.

## Run

Put the blob name in `main.py` or call the `run_extraction()` function with the blob
name you want to process:

```bash
uv run python main.py
```

The sample uses `policy.pdf` as a placeholder. It downloads to a temporary directory,
extracts content, prints a small preview, and removes the temporary file afterward.

## Important production notes

- Configure Azure RBAC for least-privilege blob access.
- The example enforces a maximum download size, but extraction accumulates page
  content in memory; this is not fully streaming end-to-end for very large PDFs.
- OCR failure is recorded in extraction errors/logging rather than being treated as
  successful OCR.
- Add structured logs, retries, durable job state, monitoring, and tests before
  deploying as a production service.
