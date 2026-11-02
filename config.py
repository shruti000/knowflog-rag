import os

from pathlib import Path
from dotenv import load_dotenv

# here we are passing the path to let know where is the env located
load_dotenv(Path(__file__).resolve().parent / ".env")

AZURE_STORAGE_ACCOUNT_URL = os.environ["AZURE_STORAGE_ACCOUNT_URL"]
AZURE_CONTAINER_NAME = os.environ["AZURE_STORAGE_CONTAINER_NAME"]
MAX_DOCUMENT_SIZE_BYTES = int(
    os.getenv("MAX_DOCUMENT_SIZE_BYTES", str(50 * 1024 * 1024))
)
