import json
from pathlib import Path

path = Path("data/embeddings/HR-Policy-embeddings.json")

with path.open("r", encoding="utf-8") as f:
    data = json.load(f)

print("Number of embedded chunks:", len(data))
print("Vector dimensions:", len(data[0]["embedding"]))
print("First chunk ID:", data[0]["chunk_id"])