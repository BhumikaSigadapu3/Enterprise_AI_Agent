from pathlib import Path
from uuid import uuid4

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.config import settings


class DocumentStore:
    def __init__(self):
        settings.chroma_dir
        self.client = chromadb.PersistentClient(path=str(Path(settings.chroma_path)))
        self.embedding = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="enterprise_knowledge",
            embedding_function=self.embedding,
        )

    def add_document(self, text: str, source: str) -> str:
        chunks = self._chunk(text)
        if not chunks:
            raise ValueError("Document contains no indexable text.")

        ids = [str(uuid4()) for _ in chunks]
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=[{"source": source} for _ in chunks],
        )
        return source

    def ensure_document(self, text: str, source: str) -> str:
        """Index a document only if this source has not already been indexed."""
        existing = self.collection.get(where={"source": source}, include=[])
        if existing.get("ids"):
            return source
        return self.add_document(text, source)

    def search(self, query: str, k: int = 4) -> list[dict]:
        count = self.collection.count()
        if count == 0:
            return []

        result = self.collection.query(
            query_texts=[query],
            n_results=min(k, count),
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        return [
            {
                "content": doc,
                "source": meta.get("source", "unknown"),
                "distance": distance,
            }
            for doc, meta, distance in zip(documents, metadatas, distances)
        ]

    @staticmethod
    def _chunk(text: str, size: int = 700, overlap: int = 100) -> list[str]:
        text = " ".join(text.split())
        if not text:
            return []
        if len(text) <= size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end])
            start += size - overlap
        return chunks


document_store = DocumentStore()
