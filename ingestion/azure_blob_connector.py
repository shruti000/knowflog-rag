from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from config import (
    AZURE_CONTAINER_NAME,
    AZURE_STORAGE_ACCOUNT_URL,
    MAX_DOCUMENT_SIZE_BYTES,
)


class AzureBlobConnector:
    """Download Azure blobs to disk without collecting the whole blob in RAM."""

    def __init__(self) -> None:
        self.credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(
            account_url=AZURE_STORAGE_ACCOUNT_URL,
            credential=self.credential,
        )
        self.container_client = self.blob_service_client.get_container_client(
            AZURE_CONTAINER_NAME
        )

    def download_to_file(
        self,
        blob_name: str,
        destination_path: Path,
    ) -> Path:
        destination_path = Path(destination_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        blob_client = self.container_client.get_blob_client(blob_name)

        properties = blob_client.get_blob_properties()
        if properties.size > MAX_DOCUMENT_SIZE_BYTES:
            raise ValueError(
                f"Document size {properties.size} bytes exceeds configured limit "
                f"{MAX_DOCUMENT_SIZE_BYTES} bytes."
            )

        downloader = blob_client.download_blob()
        bytes_written = 0

        try:
            with destination_path.open("wb") as output_file:
                for chunk in downloader.chunks():
                    bytes_written += len(chunk)
                    if bytes_written > MAX_DOCUMENT_SIZE_BYTES:
                        raise ValueError(
                            "Document exceeded configured size limit during download."
                        )
                    output_file.write(chunk)
            return destination_path
        except Exception:
            destination_path.unlink(missing_ok=True)
            raise

    def close(self) -> None:
        self.blob_service_client.close()
        self.credential.close()
