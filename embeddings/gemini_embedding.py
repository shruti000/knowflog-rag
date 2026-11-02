
import os
from typing import Any

from google import genai
from google.genai import types


class GeminiEmbedder:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-embedding-001"

    def embed_chunk(self, chunk: Any) -> dict:
        response = self.client.models.embed_content(
            model=self.model,
            contents=chunk.text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT"
            ),
        )

        embedding = response.embeddings[0].values

        return {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "embedding": embedding,
            "metadata": chunk.metadata,
        }



# RETRIEVAL_DOCUMENT -	Embedding our HR policy chunks for storage and retrieval
# RETRIEVAL_QUERY	- Embedding an employee's question when they search