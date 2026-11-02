
from pathlib import PurePosixPath


class DocumentDetector:
    SUPPORTED_TYPES = {
        ".pdf": "pdf",
        ".xlsx": "excel",
        ".xlsm": "excel",
        ".docx": "word",
        ".doc": "word",
        ".txt": "text",
    }

    @classmethod
    def detect(cls, file_name: str) -> str:
        extension = PurePosixPath(file_name).suffix.lower()

        document_type = cls.SUPPORTED_TYPES.get(extension)

        if document_type is None:
            raise ValueError(
                f"Unsupported file type: {extension}"
            )

        return document_type
